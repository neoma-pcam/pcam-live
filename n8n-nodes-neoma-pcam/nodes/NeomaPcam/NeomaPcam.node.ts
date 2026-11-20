import {
	IDataObject,
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
	NodeOperationError,
} from 'n8n-workflow';

export class NeomaPcam implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'NEOMA P-CAM',
		name: 'neomaPcam',
		icon: 'file:neomapcam.svg',
		group: ['transform'],
		version: 1,
		subtitle: '={{$parameter["operation"]}}',
		description: 'Sub-millisecond Physical AI diagnosis, 10-domain industrial risk damping, physical trust gate, and 64-spin Ising optimization',
		defaults: {
			name: 'NEOMA P-CAM',
		},
		inputs: ['main' as any],
		outputs: ['main' as any],
		credentials: [
			{
				name: 'neomaPcamApi',
				required: true,
			},
		],
		properties: [
			{
				displayName: 'Operation',
				name: 'operation',
				type: 'options',
				noDataExpression: true,
				options: [
					{
						name: 'Industrial Risk & Equilibrium Diagnosis',
						value: 'solveEquilibrium',
						description: 'Diagnose stability (zeta), compute damping control gain, and emit SEAL-PoPW receipt',
						action: 'Diagnose physical equilibrium and risk damping',
					},
					{
						name: '64-Spin Combinatorial Optimization',
						value: 'solveIsing',
						description: 'Solve scheduling, routing, or portfolio allocation via 64-spin physical Ising solver',
						action: 'Solve 64-spin Ising optimization problem',
					},
					{
						name: 'Physical Trust & Security Gate',
						value: 'trustGate',
						description: 'Hardware-rooted wave-response medium physical fingerprint trusted execution gate',
						action: 'Evaluate physical trust security gate',
					},
					{
						name: 'AI Governance & Compliance Audit',
						value: 'governanceAudit',
						description: 'Hardware-anchored zero-PRNG AI governance and EU AI Act regulatory compliance audit gate',
						action: 'Audit AI governance compliance gate',
					},
				],
				default: 'solveEquilibrium',
			},
			{
				displayName: 'Industry Domain',
				name: 'domainEndpoint',
				type: 'options',
				displayOptions: {
					show: {
						operation: ['solveEquilibrium'],
					},
				},
				options: [
					{
						name: 'Universal Operations / Supply Chain',
						value: '/v1/solve-universal-equilibrium',
					},
					{
						name: 'Quant & Financial Execution (Slippage & Liquidity)',
						value: '/v1/quant/predict',
					},
					{
						name: 'Battery & Energy Storage (Thermal Runaway & Aging)',
						value: '/v1/battery/predict',
					},
					{
						name: 'Chemical Process (Exothermic Runaway & Kinetics)',
						value: '/v1/chemistry/predict',
					},
					{
						name: 'Biopharma & Fermentation (Bioreactor Shear Stress)',
						value: '/v1/pharma/predict',
					},
					{
						name: 'Logistics & Mobility (Fleet Stability)',
						value: '/v1/mobility/predict',
					},
					{
						name: 'Robotics & Automation (Joint Compliance)',
						value: '/v1/robotics/predict',
					},
					{
						name: 'Physical Trust & Security (Wave Fingerprint Gate)',
						value: '/v1/security/trust-gate',
					},
					{
						name: 'AI Governance & Compliance (EU AI Act & Audit Gate)',
						value: '/v1/governance/audit-gate',
					},
				],
				default: '/v1/solve-universal-equilibrium',
				description: 'Select the operational domain matching your spreadsheet or database rows',
			},
			{
				displayName: 'Primary Load / Potential (flux_potential_v)',
				name: 'fluxPotentialV',
				type: 'number',
				typeOptions: { numberPrecision: 4 },
				displayOptions: {
					show: {
						operation: ['solveEquilibrium'],
					},
				},
				default: 0.5504,
				description: 'Normalized load, voltage, pressure, or order slice ratio (0.1 - 2.5)',
			},
			{
				displayName: 'Rate of Change / Velocity (gradient_velocity)',
				name: 'gradientVelocity',
				type: 'number',
				typeOptions: { numberPrecision: 2 },
				displayOptions: {
					show: {
						operation: ['solveEquilibrium'],
					},
				},
				default: 520.0,
				description: 'Speed of change, spread drift, or flow velocity (10 - 5000)',
			},
			{
				displayName: 'Shock / Acceleration (gradient_acceleration)',
				name: 'gradientAcceleration',
				type: 'number',
				typeOptions: { numberPrecision: 1 },
				displayOptions: {
					show: {
						operation: ['solveEquilibrium'],
					},
				},
				default: 16000.0,
				description: 'Sudden spike, thermal surge, or order-book depletion acceleration (100 - 100000)',
			},
			{
				displayName: 'System Stress / Strain (active_strain)',
				name: 'activeStrain',
				type: 'number',
				typeOptions: { numberPrecision: 4 },
				displayOptions: {
					show: {
						operation: ['solveEquilibrium'],
					},
				},
				default: 1.1,
				description: 'Current utilization, remaining inventory ratio, or material strain (0.1 - 2.0)',
			},
			{
				displayName: 'Number of Variables / Spins (1-64)',
				name: 'numSpins',
				type: 'number',
				typeOptions: { minValue: 1, maxValue: 64 },
				displayOptions: {
					show: {
						operation: ['solveIsing'],
					},
				},
				default: 4,
				description: 'Number of binary decision variables (up to 64 coupled nodes)',
			},
			{
				displayName: 'Node Bias Weights (JSON Array)',
				name: 'fieldsJson',
				type: 'string',
				displayOptions: {
					show: {
						operation: ['solveIsing'],
					},
				},
				default: '[-0.5, 0.5, -0.3, 0.4]',
				description: 'JSON array of individual node priorities h_i (e.g., [-0.5, 0.5, -0.3, 0.4])',
			},
			{
				displayName: 'Pairwise Couplings (JSON Array of [i, j, weight])',
				name: 'couplingsJson',
				type: 'string',
				displayOptions: {
					show: {
						operation: ['solveIsing'],
					},
				},
				default: '[[0, 1, -1.0], [1, 2, 0.8], [2, 3, -0.6]]',
				description: 'JSON array of pairwise interactions [node_i, node_j, coupling_weight]',
			},
			{
				displayName: 'Session ID',
				name: 'sessionId',
				type: 'string',
				displayOptions: { show: { operation: ['trustGate'] } },
				default: 'sess-n8n-01',
				description: 'Session identifier for trust verification',
			},
			{
				displayName: 'Action Type',
				name: 'actionType',
				type: 'string',
				displayOptions: { show: { operation: ['trustGate'] } },
				default: 'crypto_key_use',
				description: 'Action to authorize (crypto_key_use, payment_auth, robotic_command)',
			},
			{
				displayName: 'Wave Telemetry (JSON Array)',
				name: 'waveTelemetryJson',
				type: 'string',
				displayOptions: { show: { operation: ['trustGate'] } },
				default: '[0.42, 0.44, 0.41, 0.43]',
				description: 'JSON array of wave response telemetry numbers',
			},
			{
				displayName: 'Spatial Context',
				name: 'spatialContext',
				type: 'string',
				displayOptions: { show: { operation: ['trustGate'] } },
				default: 'default-enclave-zone',
				description: 'Terminal or spatial usage context',
			},
			{
				displayName: 'Liveness Score',
				name: 'livenessScore',
				type: 'number',
				typeOptions: { numberPrecision: 4 },
				displayOptions: { show: { operation: ['trustGate'] } },
				default: 0.99,
				description: 'Biometric liveness confidence score (0.0 to 1.0)',
			},
			{
				displayName: 'Agent ID',
				name: 'agentId',
				type: 'string',
				displayOptions: { show: { operation: ['governanceAudit'] } },
				default: 'agent-n8n-01',
				description: 'Autonomous agent identifier',
			},
			{
				displayName: 'Model ID',
				name: 'modelId',
				type: 'string',
				displayOptions: { show: { operation: ['governanceAudit'] } },
				default: 'frontier-reasoning-node',
				description: 'AI model identifier',
			},
			{
				displayName: 'Risk Classification',
				name: 'riskClassification',
				type: 'options',
				displayOptions: { show: { operation: ['governanceAudit'] } },
				options: [
					{ name: 'High Risk (EU AI Act)', value: 'high_risk_eu_ai_act' },
					{ name: 'Critical Infrastructure', value: 'critical_infrastructure' },
					{ name: 'Limited Risk', value: 'limited' },
					{ name: 'Minimal Risk', value: 'minimal' },
				],
				default: 'high_risk_eu_ai_act',
				description: 'Regulatory risk classification under EU AI Act & NIST RMF',
			},
			{
				displayName: 'Autonomy Pressure',
				name: 'autonomyPressure',
				type: 'number',
				typeOptions: { numberPrecision: 4 },
				displayOptions: { show: { operation: ['governanceAudit'] } },
				default: 0.35,
				description: 'Agent autonomy execution pressure (0.0 to 1.0)',
			},
			{
				displayName: 'Drift Score',
				name: 'driftScore',
				type: 'number',
				typeOptions: { numberPrecision: 4 },
				displayOptions: { show: { operation: ['governanceAudit'] } },
				default: 0.12,
				description: 'Policy/ethics deviation drift score (0.0 to 1.0)',
			},
			{
				displayName: 'Hallucination Index',
				name: 'hallucinationIndex',
				type: 'number',
				typeOptions: { numberPrecision: 4 },
				displayOptions: { show: { operation: ['governanceAudit'] } },
				default: 0.08,
				description: 'Uncertainty / hallucination index (0.0 to 1.0)',
			},
			{
				displayName: 'Human Oversight Active',
				name: 'humanOversightActive',
				type: 'boolean',
				displayOptions: { show: { operation: ['governanceAudit'] } },
				default: false,
				description: 'Whether human supervisor approval is active',
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];
		const credentials = await this.getCredentials('neomaPcamApi');

		const rawBaseUrl = String(credentials.baseUrl || 'https://neoma-p-cam-hyper-physical-control.p.rapidapi.com').replace(/\/+$/, '');
		const apiKey = String(credentials.rapidApiKey || '').trim();
		const isRapidApi = rawBaseUrl.toLowerCase().includes('rapidapi.com');

		for (let i = 0; i < items.length; i++) {
			try {
				const operation = this.getNodeParameter('operation', i) as string;
				let endpointPath = '/v1/solve-universal-equilibrium';
				let payload: IDataObject = {};

				if (operation === 'solveEquilibrium') {
					endpointPath = this.getNodeParameter('domainEndpoint', i) as string;
					payload = {
						flux_potential_v: Number(this.getNodeParameter('fluxPotentialV', i)),
						gradient_velocity: Number(this.getNodeParameter('gradientVelocity', i)),
						gradient_acceleration: Number(this.getNodeParameter('gradientAcceleration', i)),
						active_strain: Number(this.getNodeParameter('activeStrain', i)),
					};
				} else if (operation === 'solveIsing') {
					endpointPath = '/v1/ising/solve';
					const numSpins = Number(this.getNodeParameter('numSpins', i));
					const fieldsRaw = String(this.getNodeParameter('fieldsJson', i));
					const couplingsRaw = String(this.getNodeParameter('couplingsJson', i));
					payload = {
						num_spins: numSpins,
						fields: JSON.parse(fieldsRaw),
						couplings: JSON.parse(couplingsRaw),
					};
				} else if (operation === 'trustGate') {
					endpointPath = '/v1/security/trust-gate';
					let waveTelemetry = [0.42, 0.44, 0.41, 0.43];
					try {
						const rawWave = this.getNodeParameter('waveTelemetryJson', i) as string;
						if (rawWave) waveTelemetry = JSON.parse(rawWave);
					} catch {}
					payload = {
						session_id: String(this.getNodeParameter('sessionId', i) || 'sess-n8n-01'),
						action_type: String(this.getNodeParameter('actionType', i) || 'crypto_key_use'),
						wave_telemetry: waveTelemetry,
						spatial_context: String(this.getNodeParameter('spatialContext', i) || 'default-enclave-zone'),
						liveness_score: Number(this.getNodeParameter('livenessScore', i) || 0.99),
					};
				} else if (operation === 'governanceAudit') {
					endpointPath = '/v1/governance/audit-gate';
					payload = {
						agent_id: String(this.getNodeParameter('agentId', i) || 'agent-n8n-01'),
						model_id: String(this.getNodeParameter('modelId', i) || 'frontier-reasoning-node'),
						risk_classification: String(this.getNodeParameter('riskClassification', i) || 'high_risk_eu_ai_act'),
						autonomy_pressure: Number(this.getNodeParameter('autonomyPressure', i) || 0.35),
						drift_score: Number(this.getNodeParameter('driftScore', i) || 0.12),
						hallucination_index: Number(this.getNodeParameter('hallucinationIndex', i) || 0.08),
						human_oversight_active: Boolean(this.getNodeParameter('humanOversightActive', i) || false),
					};
				} else {
					throw new NodeOperationError(this.getNode(), `Unsupported operation: ${operation}`, { itemIndex: i });
				}

				const headers: Record<string, string> = {
					'Content-Type': 'application/json',
				};
				if (isRapidApi && apiKey) {
					headers['x-rapidapi-key'] = apiKey;
					headers['x-rapidapi-host'] = new URL(rawBaseUrl).host;
				}

				const response = await fetch(`${rawBaseUrl}${endpointPath}`, {
					method: 'POST',
					headers,
					body: JSON.stringify(payload),
				});

				if (!response.ok) {
					const errText = await response.text();
					throw new NodeOperationError(
						this.getNode(),
						`NEOMA P-CAM API returned HTTP ${response.status}: ${errText}`,
						{ itemIndex: i },
					);
				}

				const result = (await response.json()) as IDataObject;

				if (operation === 'solveEquilibrium') {
					const zeta = Number(result.zeta ?? 1.0);
					const intensity = Number(result.control_intensity ?? 0.5);
					const mode = Number(result.state_mode ?? 2);
					result.action_recommendation =
						mode === 3
							? `SHOCK_OVERDAMPED (zeta=${zeta.toFixed(4)}): Apply ${Math.round(intensity * 100)}% damping throttle immediately.`
							: `EQUILIBRIUM_STABLE (zeta=${zeta.toFixed(4)}): Safe to operate at ${Math.round(intensity * 100)}% optimal gain.`;
				}

				returnData.push({
					json: result,
					pairedItem: { item: i },
				});
			} catch (error) {
				if (this.continueOnFail()) {
					returnData.push({
						json: { error: (error as Error).message },
						pairedItem: { item: i },
					});
					continue;
				}
				throw error;
			}
		}

		return [returnData];
	}
}