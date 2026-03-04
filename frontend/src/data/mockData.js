// src/data/mockData.js
export const agents = [
  { id: 'a1', role: 'TrendRadar', model: 'llama3-8b-8192', latency: '45ms', successRate: '98%', costPerTask: 0.005, active: true },
  { id: 'a2', role: 'ViralJudge', model: 'gpt-4o-mini', latency: '210ms', successRate: '95%', costPerTask: 0.02, active: true },
  { id: 'a3', role: 'MonetizationScorer', model: 'gpt-4o-mini', latency: '190ms', successRate: '96%', costPerTask: 0.02, active: true },
  { id: 'a4', role: 'ScriptArchitect', model: 'gpt-4o', latency: '850ms', successRate: '92%', costPerTask: 0.15, active: true },
  { id: 'a5', role: 'HookOptimizer', model: 'claude-3-5-sonnet', latency: '540ms', successRate: '94%', costPerTask: 0.08, active: true },
  { id: 'a6', role: 'RiskGuard', model: 'gpt-4o-mini', latency: '120ms', successRate: '99%', costPerTask: 0.01, active: true },
  { id: 'a7', role: 'VideoDirector', model: 'gpt-4o', latency: '1200ms', successRate: '88%', costPerTask: 0.20, active: true },
  { id: 'a8', role: 'Publisher', model: 'API Connector', latency: '350ms', successRate: '97%', costPerTask: 0.00, active: true },
  { id: 'a9', role: 'GrowthAnalyst', model: 'llama3-70b-8192', latency: '400ms', successRate: '93%', costPerTask: 0.05, active: true },
  { id: 'a10', role: 'ProfitManager', model: 'gpt-4o-mini', latency: '200ms', successRate: '99%', costPerTask: 0.02, active: true }
];

export const trends = [
  { id: 't1', title: 'Tech Gadget Hacks 2026', viralScore: 92, moneyScore: 88, finalScore: 90, status: 'approved' },
  { id: 't2', title: 'Wealth Building Mistakes', viralScore: 85, moneyScore: 95, finalScore: 89, status: 'processing' },
  { id: 't3', title: 'Hidden iPhone Settings', viralScore: 98, moneyScore: 60, finalScore: 83, status: 'review' },
  { id: 't4', title: 'Day in Life of AI Agents', viralScore: 75, moneyScore: 85, finalScore: 79, status: 'rejected' }
];

export const runs = [
  { id: 'run-morning-0303', name: 'Morning cycle', status: 'completed', cost: 1.45, duration: '12m 34s', time: '08:00 AM' },
  { id: 'run-evening-0303', name: 'Evening cycle', status: 'running', cost: 0.82, duration: '5m 12s', time: '04:00 PM' },
  { id: 'run-morning-0302', name: 'Morning cycle', status: 'completed', cost: 1.55, duration: '14m 05s', time: '08:00 AM' },
];

export const messages = [
  { id: 'm1', content_id: 't2', from_agent: 'TrendRadar', to_agent: 'ViralJudge', type: 'propose', summary: 'Found high-momentum trend on Wealth Mistakes', payload: { search_volume: '+450%', competition: 'medium' }, status: 'completed', timestamp: '16:01:05' },
  { id: 'm2', content_id: 't2', from_agent: 'ViralJudge', to_agent: 'MonetizationScorer', type: 'vote', summary: 'Confirmed viral potential (85/100). High retention expected with controversial hook.', payload: { retention_est: '55% @ 3s', emotion_trigger: 'FOMO' }, status: 'completed', timestamp: '16:01:25' },
  { id: 'm3', content_id: 't2', from_agent: 'MonetizationScorer', to_agent: 'ScriptArchitect', type: 'vote', summary: 'Monetization is excellent (95/100). Affiliates match perfectly.', payload: { est_epm: '$8.50', sponsor_fit: 'high' }, status: 'completed', timestamp: '16:01:45' },
  { id: 'm4', content_id: 't2', from_agent: 'ScriptArchitect', to_agent: 'HookOptimizer', type: 'deliver', summary: 'Drafted 45s script. Need 3 hook variants.', payload: { word_count: 120, format: 'listicle' }, status: 'completed', timestamp: '16:03:10' },
  { id: 'm5', content_id: 't2', from_agent: 'HookOptimizer', to_agent: 'RiskGuard', type: 'propose', summary: 'Generated Hooks. Hook 1 is most aggressive.', payload: { selected_hook: '"You are losing $5,000 every year because of this hidden bank fee..."' }, status: 'pending', timestamp: '16:03:30' },
  { id: 'm6', content_id: 't2', from_agent: 'RiskGuard', to_agent: 'VideoDirector', type: 'alert', summary: 'Hook 1 triggered financial advice warning. Downgrading to Hook 2.', payload: { risk_score: 85, action: 'override_hook', new_hook: '"Most people make this money mistake without knowing..."' }, status: 'pending', timestamp: '16:03:35' },
];

export const contents = [
  { id: 'c1', title: 'Tech Gadget Hacks 2026', column: 'Posted', viralScore: 92, moneyScore: 88, finalScore: 90, riskScore: 5, costEstimate: 0.65, assignedAgent: 'Publisher' },
  { id: 'c2', title: 'Dark Psychology Tricks', column: 'Ideas', viralScore: 95, moneyScore: 40, finalScore: 73, riskScore: 80, costEstimate: 0.15, assignedAgent: 'TrendRadar' },
  { id: 'c3', title: 'Wealth Building Mistakes', column: 'Script', viralScore: 85, moneyScore: 95, finalScore: 89, riskScore: 15, costEstimate: 0.30, assignedAgent: 'ScriptArchitect' },
  { id: 'c4', title: 'AI Tools You Need Now', column: 'Review', viralScore: 88, moneyScore: 82, finalScore: 85, riskScore: 10, costEstimate: 0.85, assignedAgent: 'VideoDirector' },
  { id: 'c5', title: 'Minimalist Desk Setup', column: 'Media', viralScore: 75, moneyScore: 90, finalScore: 81, riskScore: 5, costEstimate: 0.50, assignedAgent: 'VideoDirector' }
];

export const approvals = [
  { id: 'ap1', type: 'topic', title: 'Controversial AI Predictions', viralScore: 95, moneyScore: 70, finalScore: 85, cost: 0.05, preview: 'Will AI replace software engineers in 3 years? Focus on coding automation tools.' },
  { id: 'ap2', type: 'script', title: 'Passive Income Myth', viralScore: 82, moneyScore: 92, finalScore: 86, cost: 0.35, preview: '[Hook] Stop trying to build "passive income" streams... do this instead.' },
  { id: 'ap3', type: 'video', title: 'Notion Template Tour', viralScore: 80, moneyScore: 98, finalScore: 87, cost: 1.20, preview: 'Finished MP4 generation (38s). Features UI screencasts and trending audio.' }
];

export const runMetrics = [
  { name: 'Mon', morning: 85, evening: 92 },
  { name: 'Tue', morning: 78, evening: 88 },
  { name: 'Wed', morning: 95, evening: 84 },
  { name: 'Thu', morning: 82, evening: 91 },
  { name: 'Fri', morning: 90, evening: 98 },
  { name: 'Sat', morning: 96, evening: 75 },
  { name: 'Sun', morning: 88, evening: 85 },
];
