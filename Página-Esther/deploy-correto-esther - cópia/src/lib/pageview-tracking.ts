// 1. GERAÇÃO DE SESSION ID ÚNICO
export function generateSessionId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 15)}-${Math.random().toString(36).substring(2, 15)}`;
}

export function getOrCreateSessionId(): string {
  const storageKey = 'tracking_session_id';
  let sessionId = sessionStorage.getItem(storageKey);

  if (!sessionId) {
    sessionId = generateSessionId();
    sessionStorage.setItem(storageKey, sessionId);
  }

  return sessionId;
}

// 2. CAPTURA DE COOKIES
export function getCookie(name: string): string {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop()?.split(';').shift() || '';
  }
  return '';
}

// 3. GERAR FBC A PARTIR DO FBCLID
export function getFbcFromUrl(): string {
  const params = new URLSearchParams(window.location.search);
  const fbclid = params.get('fbclid');

  if (fbclid) {
    const timestamp = Date.now();
    return `fb.1.${timestamp}.${fbclid}`;
  }

  return '';
}

// 4. CAPTURA DE IP
export async function getUserIP(): Promise<string> {
  try {
    const response = await fetch('https://api.ipify.org?format=json');
    const data = await response.json();
    return data.ip || '';
  } catch (error) {
    console.error('Erro ao capturar IP:', error);
    return '';
  }
}

// 5. CONTROLE DE ENVIO (UMA VEZ POR DIA)
let isSendingPageView = false;

export function hasPageViewSentToday(): boolean {
  try {
    const lastSent = localStorage.getItem('pageview_last_sent');
    if (!lastSent) return false;

    const today = new Date().toDateString();
    return lastSent === today;
  } catch (error) {
    console.error('Erro ao verificar PageView:', error);
    return false;
  }
}

export function markPageViewSent(): void {
  try {
    const today = new Date().toDateString();
    localStorage.setItem('pageview_last_sent', today);
  } catch (error) {
    console.error('Erro ao marcar PageView:', error);
  }
}

type LeadData = {
  email?: string;
  phone?: string;
  birthday?: string;
  name?: string;
};

export function getLeadFromStorage(): LeadData {
  try {
    const raw = localStorage.getItem('tracking_lead_data');
    if (!raw) return {};
    const parsed = JSON.parse(raw) as LeadData;
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch {
    return {};
  }
}

// 6. FUNÇÃO PRINCIPAL: ENVIAR PAGEVIEW
export async function sendPageViewEvent() {
  // Evitar envio duplicado
  if (isSendingPageView) {
    console.log('PageView já está sendo enviado');
    return;
  }

  try {
    // Verificar se já enviou hoje
    if (hasPageViewSentToday()) {
      console.log('PageView já enviado hoje');
      return;
    }

    // Marcar como enviando
    isSendingPageView = true;

    const params = new URLSearchParams(window.location.search);

    // Capturar IP
    const ip = await getUserIP();

    const lead = getLeadFromStorage();

    // Montar payload
    const pageViewData = {
      event: 'PageView',
      timestamp: Date.now(),
      session_id: getOrCreateSessionId(),

      // Lead (se disponível no storage)
      email: lead.email || '',
      phone: lead.phone || '',
      birthday: lead.birthday || '',
      name: lead.name || '',

      // Parâmetros de anúncios
      fbclid: params.get('fbclid') || '',
      fbc: params.get('fbclid') ? getFbcFromUrl() : '',
      fbp: getCookie('_fbp'),
      gclid: params.get('gclid') || '',
      gbraid: params.get('gbraid') || '',
      wbraid: params.get('wbraid') || '',
      ttclid: params.get('ttclid') || '',
      msclkid: params.get('msclkid') || '',

      // UTMs
      utm_source: params.get('utm_source') || '',
      utm_medium: params.get('utm_medium') || '',
      utm_campaign: params.get('utm_campaign') || '',
      utm_content: params.get('utm_content') || '',
      utm_term: params.get('utm_term') || '',

      // Dados da página
      page_url: window.location.href,
      page_title: document.title,

      // Dados do dispositivo
      user_agent: navigator.userAgent,
      ip,
    };

    // Enviar para webhook
    await fetch('https://n8n.srv1185225.hstgr.cloud/webhook/page-view-esther', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pageViewData),
    });

    // Marcar como enviado hoje
    markPageViewSent();

    console.log('PageView event sent successfully');
  } catch (error) {
    console.error('Erro ao enviar PageView event:', error);
  } finally {
    // Resetar flag após 1 segundo
    setTimeout(() => {
      isSendingPageView = false;
    }, 1000);
  }
}

