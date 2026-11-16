"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.NeomaPcamApi = void 0;
class NeomaPcamApi {
    name = 'neomaPcamApi';
    displayName = 'NEOMA P-CAM API';
    documentationUrl = 'https://neoma-pcam.github.io/pcam-live/';
    properties = [
        {
            displayName: 'RapidAPI Key',
            name: 'rapidApiKey',
            type: 'string',
            typeOptions: { password: true },
            default: '',
            required: true,
            description: 'Your RapidAPI key (2,000 free calls/month on Universal Solver, or Quant/Enterprise tier)',
        },
        {
            displayName: 'Gateway Base URL',
            name: 'baseUrl',
            type: 'string',
            default: 'https://neoma-p-cam-hyper-physical-control.p.rapidapi.com',
            description: 'Default RapidAPI gateway or direct enterprise enclave URL (https://api.neoma-pcam.com)',
        },
    ];
    authenticate = {
        type: 'generic',
        properties: {
            headers: {
                'x-rapidapi-key': '={{$credentials.rapidApiKey}}',
                'x-rapidapi-host': 'neoma-p-cam-hyper-physical-control.p.rapidapi.com',
            },
        },
    };
    test = {
        request: {
            baseURL: '={{$credentials.baseUrl}}',
            url: '/v1/solve-universal-equilibrium',
            method: 'POST',
            body: {
                flux_potential_v: 0.5504,
                gradient_velocity: 520.0,
                gradient_acceleration: 16000.0,
                active_strain: 1.1,
            },
        },
    };
}
exports.NeomaPcamApi = NeomaPcamApi;
//# sourceMappingURL=NeomaPcamApi.credentials.js.map