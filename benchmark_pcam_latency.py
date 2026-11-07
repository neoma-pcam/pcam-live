import time
import torch
import torch.nn as nn
from transformers import AutoConfig, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

BASE_MODEL = "microsoft/Phi-3-mini-4k-instruct"
ADAPTER_DIR = "./pcam_phi3_adapter"
PROJECTOR_WEIGHTS = "pcam_projector.pt"
DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"

class PCAMPhysicalProjector(nn.Module):
    def __init__(self, in_features=4, hidden_dim=512, out_dim=3072):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, out_dim),
            nn.LayerNorm(out_dim)
        )

    def forward(self, x):
        return self.net(x)

print("[*] 벤치마크 환경 초기화 중 (GTX 1650 CUDA Event 타이머 준비)...")

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=False)
special_tokens = {"additional_special_tokens": ["<|pcam_q12|>", "<|end_pcam|>"]}
tokenizer.add_special_tokens(special_tokens)

config = AutoConfig.from_pretrained(BASE_MODEL, trust_remote_code=False)
if hasattr(config, "rope_scaling") and config.rope_scaling:
    if "type" not in config.rope_scaling:
        config.rope_scaling["type"] = config.rope_scaling.get("rope_type", "longrope")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True
)

base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    config=config,
    quantization_config=bnb_config,
    device_map={"": 0},
    trust_remote_code=False
)
base_model.resize_token_embeddings(len(tokenizer))

model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
model.eval()

embedding_layer = model.get_input_embeddings()
TARGET_DTYPE = embedding_layer.weight.dtype

projector = PCAMPhysicalProjector().to(device=DEVICE, dtype=TARGET_DTYPE)
projector.load_state_dict(torch.load(PROJECTOR_WEIGHTS, map_location=DEVICE))
projector.eval()

# 테스트 입력 텐서 준비
raw_q12 = torch.tensor([[348.0, 2048.0, 3482.0, 141.0]], device=DEVICE, dtype=TARGET_DTYPE) / 4096.0
prefix_ids = tokenizer("<|user|>\n", return_tensors="pt").input_ids.to(DEVICE)
suffix_ids = tokenizer("\nGenerate reflex action and macroscopic physical wear analysis.<|end|>\n<|assistant|>\n", return_tensors="pt").input_ids.to(DEVICE)

prefix_embeds = embedding_layer(prefix_ids)
suffix_embeds = embedding_layer(suffix_ids)

# 웜업(Warm-up): CUDA 커널 초기 로딩 지연 제거
print("[*] GPU 캐시 워밍업 실행 중 (3회)...")
with torch.no_grad():
    for _ in range(3):
        p_embed = projector(raw_q12).unsqueeze(1)
        c_embed = torch.cat([prefix_embeds, p_embed, suffix_embeds], dim=1)
        _ = model.generate(inputs_embeds=c_embed, max_new_tokens=5, do_sample=False)
torch.cuda.synchronize()

print("[*] 정밀 벤치마크 측정 시작...")

# 1. 프로젝터 텐서 투사 지연 시간 측정 (CUDA Event 기반)
start_event = torch.cuda.Event(enable_timing=True)
end_event = torch.cuda.Event(enable_timing=True)

start_event.record()
with torch.no_grad():
    phys_embed = projector(raw_q12).unsqueeze(1)
end_event.record()
torch.cuda.synchronize()
projector_latency_ms = start_event.elapsed_time(end_event)

# 2. 반사 응답(TTFT: Time To First Token) 측정
combined_embeds = torch.cat([prefix_embeds, phys_embed, suffix_embeds], dim=1)
attention_mask = torch.ones(combined_embeds.shape[:2], dtype=torch.long, device=DEVICE)

start_event.record()
with torch.no_grad():
    first_token_out = model.generate(
        inputs_embeds=combined_embeds,
        attention_mask=attention_mask,
        max_new_tokens=1,
        min_new_tokens=1,
        do_sample=False
    )
end_event.record()
torch.cuda.synchronize()
ttft_latency_ms = start_event.elapsed_time(end_event)

# 3. 전체 물리 진단 시퀀스 생성(End-to-End) 측정
start_event.record()
with torch.no_grad():
    full_output = model.generate(
        inputs_embeds=combined_embeds,
        attention_mask=attention_mask,
        max_new_tokens=120,
        min_new_tokens=30,
        do_sample=False
    )
end_event.record()
torch.cuda.synchronize()
total_latency_ms = start_event.elapsed_time(end_event)

generated_tokens = full_output.shape[1]
throughput = (generated_tokens / total_latency_ms) * 1000

print("\n" + "=" * 65)
print(" [P-CAM 텐서 직결 하드웨어 벤치마크 결과]")
print("=" * 65)
print(f"1. 프로젝터 사영 지연 (4ch -> 3072차원) : {projector_latency_ms:.3f} ms ({projector_latency_ms*1000:.1f} μs)")
print(f"2. 하드웨어 반사 첫 토큰(TTFT) 지연   : {ttft_latency_ms:.2f} ms")
print(f"3. 전체 진단문 생성 시간 ({generated_tokens} 토큰) : {total_latency_ms:.2f} ms")
print(f"4. 실시간 토큰 생성 처리율 (Throughput) : {throughput:.2f} tokens/sec")
print("=" * 65)