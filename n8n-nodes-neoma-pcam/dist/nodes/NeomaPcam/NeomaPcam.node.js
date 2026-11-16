"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.NeomaPcam = void 0;
const n8n_workflow_1 = require("n8n-workflow");
class NeomaPcam {
    description = {
        displayName: 'NEOMA P-CAM',
        name: 'neomaPcam',
        icon: 'file:neomapcam.svg',
        group: ['transform'],
        version: 1,
        subtitle: '={{$parameter["operation"]}}',
        description: 'Sub-millisecond Physical AI diagnosis, industrial risk damping, and 64-spin Ising optimization',
        defaults: {
            name: 'NEOMA P-CAM',
        },
        inputs: ['main'],
        outputs: ['main'],
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
        ],
    };
    async execute() {
        const items = this.getInputData();
        const returnData = [];
        const credentials = await this.getCredentials('neomaPcamApi');
        const rawBaseUrl = String(credentials.baseUrl || 'https://neoma-p-cam-hyper-physical-control.p.rapidapi.com').replace(/\/+$/, '');
        const apiKey = String(credentials.rapidApiKey || '').trim();
        const isRapidApi = rawBaseUrl.toLowerCase().includes('rapidapi.com');
        for (let i = 0; i < items.length; i++) {
            try {
                const operation = this.getNodeParameter('operation', i);
                let endpointPath = '/v1/solve-universal-equilibrium';
                let payload = {};
                if (operation === 'solveEquilibrium') {
                    endpointPath = this.getNodeParameter('domainEndpoint', i);
                    payload = {
                        flux_potential_v: Number(this.getNodeParameter('fluxPotentialV', i)),
                        gradient_velocity: Number(this.getNodeParameter('gradientVelocity', i)),
                        gradient_acceleration: Number(this.getNodeParameter('gradientAcceleration', i)),
                        active_strain: Number(this.getNodeParameter('activeStrain', i)),
                    };
                }
                else if (operation === 'solveIsing') {
                    endpointPath = '/v1/ising/solve';
                    const numSpins = Number(this.getNodeParameter('numSpins', i));
                    const fieldsRaw = String(this.getNodeParameter('fieldsJson', i));
                    const couplingsRaw = String(this.getNodeParameter('couplingsJson', i));
                    payload = {
                        num_spins: numSpins,
                        fields: JSON.parse(fieldsRaw),
                        couplings: JSON.parse(couplingsRaw),
                    };
                }
                else {
                    throw new n8n_workflow_1.NodeOperationError(this.getNode(), `Unsupported operation: ${operation}`, { itemIndex: i });
                }
                const headers = {
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
                    throw new n8n_workflow_1.NodeOperationError(this.getNode(), `NEOMA P-CAM API returned HTTP ${response.status}: ${errText}`, { itemIndex: i });
                }
                const result = (await response.json());
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
            }
            catch (error) {
                if (this.continueOnFail()) {
                    returnData.push({
                        json: { error: error.message },
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
exports.NeomaPcam = NeomaPcam;
//# sourceMappingURL=NeomaPcam.node.js.map