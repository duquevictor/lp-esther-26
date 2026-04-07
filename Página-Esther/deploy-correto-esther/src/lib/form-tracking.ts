// ============================================
// BIBLIOTECA DE FORM TRACKING
// ============================================

import {
  getOrCreateSessionId,
  getCookie,
  getFbcFromUrl,
  getUserIP,
} from './pageview-tracking';

// 1. DETERMINAR MOEDA POR PAÍS
export function getCurrency(countryCode: string): string {
  return countryCode === 'BR' ? 'BRL' : 'USD';
}

// 2. CAPTURA COMPLETA DE DADOS DO FORMULÁRIO
export async function captureTrackingData(
  email: string,
  phone: string,
  birthday: string,
  name?: string
) {
  const params = new URLSearchParams(window.location.search);
  const ip = await getUserIP();
  const fbclid = params.get('fbclid') || '';
  const fbc = fbclid ? getFbcFromUrl() : '';

  const trackingData = {
    email,
    phone,
    birthday,
    ...(name && { name }),
    session_id: getOrCreateSessionId(),
    fbclid,
    fbc,
    fbp: getCookie('_fbp'),
    gclid: params.get('gclid') || '',
    gbraid: params.get('gbraid') || '',
    wbraid: params.get('wbraid') || '',
    ttclid: params.get('ttclid') || '',
    msclkid: params.get('msclkid') || '',
    utm_source: params.get('utm_source') || '',
    utm_medium: params.get('utm_medium') || '',
    utm_campaign: params.get('utm_campaign') || '',
    utm_content: params.get('utm_content') || '',
    utm_term: params.get('utm_term') || '',
    page_url: window.location.href,
    referrer: document.referrer,
    ip,
    Currency: 'BRL',
    user_agent: navigator.userAgent,
    timestamp: Date.now(),
  };

  // Persistência para acessos futuros
  localStorage.setItem('lead_email', email);
  if (name) localStorage.setItem('lead_name', name);

  return trackingData;
}

// 3. ENVIAR PARA MÚLTIPLOS WEBHOOKS
export async function sendTrackingData(trackingData: any) {
  const results = {
    trackCookies: false,
    leadIndividual: false,
    registerLead: false,
  };

  try {
    // WEBHOOK 1: Track Cookies (Removendo o nome para este endpoint)
    const trackDataWithoutName = { ...trackingData };
    delete trackDataWithoutName.name;

    const trackResponse = await fetch(
      'https://n8n.srv1185225.hstgr.cloud/webhook/track-cookies-esther',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(trackDataWithoutName),
      }
    );
    results.trackCookies = trackResponse.ok;

    // WEBHOOK 2: Initiate Checkout / Tag Lead
    const leadResponse = await fetch(
      'https://n8n.srv1185225.hstgr.cloud/webhook/initiate-esther',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(trackingData),
      }
    );
    results.leadIndividual = leadResponse.ok;

    // WEBHOOK 3: Registro de Lead (Dados do Produto)
    const productLeadPayload = {
      nome: trackingData.name || '',
      whatsapp: trackingData.phone,
      email: trackingData.email,
      dataNascimento: trackingData.birthday,
      tag: 'Assunto Infinito Black',
      pageTitle: document.title,
      pageUrl: window.location.href,
      utm_source: trackingData.utm_source,
      utm_medium: trackingData.utm_medium,
      utm_campaign: trackingData.utm_campaign,
      utm_term: trackingData.utm_term,
      utm_content: trackingData.utm_content,
      nome_produto: 'Assunto Infinito Black',
      preco_produto: 197.0,
      produto_id: '41258d80-1344-4000-b9e4-29ed020d498e',
    };

    const registerResponse = await fetch(
      'https://n8n.srv1185225.hstgr.cloud/webhook/2ea8031d-58c9-45f4-942e-a6aae309cebb',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(productLeadPayload),
      }
    );
    results.registerLead = registerResponse.ok;

    return results;
  } catch (error) {
    console.error('Erro ao enviar tracking data:', error);
    return results;
  }
}

