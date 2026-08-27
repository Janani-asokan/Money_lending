import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import * as Icons from 'lucide-react';
import './styles.css';

const API = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');
const IS_DEMO = import.meta.env.VITE_SHOW_DEMO_ACCOUNTS === 'true';
const FallbackIcon = ({ size = 18 }) => <span style={{ width: size, height: size, display: 'inline-block' }} />;
const AlertTriangle = Icons.AlertTriangle || Icons.TriangleAlert || FallbackIcon;
const AreaChart = Icons.AreaChart || Icons.ChartArea || Icons.BarChart3 || FallbackIcon;
const BadgeIndianRupee = Icons.BadgeIndianRupee || Icons.IndianRupee || FallbackIcon;
const Bell = Icons.Bell || FallbackIcon;
const Calculator = Icons.Calculator || FallbackIcon;
const CalendarClock = Icons.CalendarClock || Icons.Calendar || FallbackIcon;
const CircleGauge = Icons.CircleGauge || Icons.Gauge || FallbackIcon;
const CheckCircle2 = Icons.CheckCircle2 || Icons.CircleCheck || FallbackIcon;
const ChevronRight = Icons.ChevronRight || FallbackIcon;
const ContactRound = Icons.ContactRound || Icons.UserRound || FallbackIcon;
const CreditCard = Icons.CreditCard || FallbackIcon;
const DatabaseBackup = Icons.DatabaseBackup || Icons.Database || FallbackIcon;
const Download = Icons.Download || FallbackIcon;
const Eye = Icons.Eye || FallbackIcon;
const EyeOff = Icons.EyeOff || FallbackIcon;
const FileBarChart2 = Icons.FileBarChart2 || Icons.FileChartColumn || Icons.FileText || FallbackIcon;
const FileText = Icons.FileText || FallbackIcon;
const Globe2 = Icons.Globe2 || Icons.Globe || FallbackIcon;
const LayoutDashboard = Icons.LayoutDashboard || Icons.Gauge || FallbackIcon;
const LockKeyhole = Icons.LockKeyhole || Icons.Lock || FallbackIcon;
const LogOut = Icons.LogOut || FallbackIcon;
const Moon = Icons.Moon || FallbackIcon;
const Plus = Icons.Plus || FallbackIcon;
const Printer = Icons.Printer || FallbackIcon;
const ReceiptIndianRupee = Icons.ReceiptIndianRupee || Icons.Receipt || Icons.IndianRupee || FallbackIcon;
const Search = Icons.Search || FallbackIcon;
const SearchCheck = Icons.SearchCheck || Icons.Search || FallbackIcon;
const Settings = Icons.Settings || FallbackIcon;
const ShieldCheck = Icons.ShieldCheck || FallbackIcon;
const Sparkles = Icons.Sparkles || FallbackIcon;
const Sun = Icons.Sun || FallbackIcon;
const Target = Icons.Target || FallbackIcon;
const Users = Icons.Users || FallbackIcon;
const WalletCards = Icons.WalletCards || Icons.Wallet || FallbackIcon;
const X = Icons.X || FallbackIcon;

const TEXT = {
  en: {
    title: 'Sri Sakthi Thirumurugan Finance',
    subtitle: 'Enterprise NBFC Operations Platform',
    dashboard: 'Dashboard',
    customers: 'Customers',
    loans: 'Loans',
    collections: 'Collections',
    search: 'Search',
    reports: 'Reports',
    audit: 'Audit',
    settings: 'Settings',
    login: 'Sign in',
    owner: 'Owner',
    manager: 'Manager',
    collector: 'Collector',
    accountant: 'Accountant'
  },
  ta: {
    title: 'ஸ்ரீ திருமுருகன் பைனான்ஸ்',
    subtitle: 'கடன் மேலாண்மை அமைப்பு',
    dashboard: 'டாஷ்போர்டு',
    customers: 'வாடிக்கையாளர்கள்',
    loans: 'கடன்கள்',
    collections: 'வசூல்',
    search: 'தேடல்',
    reports: 'அறிக்கைகள்',
    audit: 'ஆடிட்',
    settings: 'அமைப்புகள்',
    login: 'உள்நுழை',
    owner: 'உரிமையாளர்',
    manager: 'மேலாளர்',
    collector: 'கலெக்டர்',
    accountant: 'கணக்காளர்'
  }
};

function useApi(setUser) {
  return async (path, options = {}) => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 20000);
    let res;
    try {
      res = await fetch(`${API}${path}`, {
        ...options,
        credentials: 'include',
        signal: options.signal || controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {})
        }
      });
    } catch (error) {
      if (error.name === 'AbortError') throw new Error('The server took too long to respond. Please try again.');
      throw new Error('Cannot reach the server. Check your connection and try again.');
    } finally {
      window.clearTimeout(timeout);
    }
    if (res.status === 401 && !path.startsWith('/api/auth/')) {
      const refreshed = await fetch(`${API}/api/auth/refresh`, { method: 'POST', credentials: 'include' });
      if (refreshed.ok) {
        return fetch(`${API}${path}`, { ...options, credentials: 'include', headers: { 'Content-Type': 'application/json', ...(options.headers || {}) } }).then(async retry => {
          if (!retry.ok) throw new Error((await retry.json().catch(()=>({}))).detail || 'Request failed');
          return retry.json();
        });
      }
      setUser(null);
    }
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      if ([502, 503, 504].includes(res.status)) {
        throw new Error('Service temporarily unavailable. Your saved data is safe. Please try again in a few moments.');
      }
      throw new Error(body.detail || 'Request failed');
    }
    return res.json();
  };
}

function App() {
  const [user, setUser] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [view, setView] = useState('dashboard');
  const [theme, setTheme] = useState(localStorage.getItem('stf_theme') || 'light');
  const [lang, setLang] = useState(localStorage.getItem('stf_lang') || 'en');
  const [toast, setToast] = useState('');
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(false);
  const api = useApi(setUser);
  const t = lang === 'ta' ? {
    ...TEXT.en,
    title: 'Sri Sakthi Thirumurugan Finance',
    subtitle: 'Tamil and English Lending Platform'
  } : TEXT.en;

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('stf_theme', theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('stf_lang', lang);
  }, [lang]);

  useEffect(() => {
    api('/api/me').then(setUser).catch(() => setUser(null)).finally(() => setAuthChecked(true));
  }, []);

  useEffect(() => {
    const handler = e => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setPaletteOpen(true);
      }
      if (e.key === 'Escape') setPaletteOpen(false);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  if (!authChecked) return <Skeleton />;
  if (!user) {
    return <Login t={t} setUser={setUser} api={api} theme={theme} setTheme={setTheme} lang={lang} setLang={setLang} />;
  }

  const nav = [
    ['dashboard', t.dashboard, LayoutDashboard, true],
    ['customers', t.customers, Users, ['owner', 'manager', 'accountant'].includes(user.role)],
    ['profile', 'Customer 360', ContactRound, ['owner', 'manager', 'accountant'].includes(user.role)],
    ['loans', t.loans, CreditCard, ['owner', 'manager', 'accountant'].includes(user.role)],
    ['collections', t.collections, ReceiptIndianRupee, ['owner', 'manager', 'collector'].includes(user.role)],
    ['planner', 'EMI Planner', Calculator, true],
    ['search', t.search, Search, true],
    ['reports', t.reports, FileBarChart2, ['owner', 'manager', 'accountant'].includes(user.role)],
    ['audit', t.audit, ShieldCheck, user.role === 'owner'],
    ['settings', t.settings, Settings, user.role === 'owner'],
    ['accounting', 'Accounting', WalletCards, ['owner', 'manager', 'accountant'].includes(user.role)]
  ].filter(x => x[3]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><img src="/logo-mark.svg" alt="" /></div>
          <div>
            <strong>{t.title}</strong>
            <span>{t.subtitle}</span>
          </div>
        </div>
        <nav>
          {nav.map(([id, label, Icon]) => (
            <button key={id} className={view === id ? 'nav-item active' : 'nav-item'} onClick={() => setView(id)}>
              <Icon size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-card">
          <ShieldCheck size={18} />
          <div>
            <strong>Protected workspace</strong>
            <span>Aadhaar-safe records, role controls, and a complete audit trail.</span>
          </div>
        </div>
      </aside>

      <main>
        <header className="topbar">
          <div>
            <div className="eyebrow">Secure role workspace</div>
            <h1>{viewTitle(view, t)}</h1>
          </div>
          <div className="top-actions">
            <button className="search-trigger" title="Command palette" onClick={() => setPaletteOpen(true)}><Search size={17} /> Ctrl K</button>
            <button className="icon-btn notification-btn" title="Notifications" onClick={() => setNotificationsOpen(true)}><Bell size={18} /><i /></button>
            <button className="icon-btn" title="Language" onClick={() => setLang(lang === 'en' ? 'ta' : 'en')}><Globe2 size={18} /></button>
            <button className="icon-btn" title="Theme" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>{theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}</button>
            <div className="user-chip">
              <span>{user.name}</span>
              <small>{t[user.role]}</small>
            </div>
            <button className="icon-btn" title="Logout" onClick={async () => { try { await api('/api/auth/logout', {method:'POST'}); } finally { setUser(null); } }}><LogOut size={18} /></button>
          </div>
        </header>

        {toast && <div className="toast">{toast}</div>}
        {paletteOpen && <CommandPalette onClose={() => setPaletteOpen(false)} onSelect={id => { setView(id); setPaletteOpen(false); }} />}
        {notificationsOpen && <NotificationCenter api={api} onClose={() => setNotificationsOpen(false)} />}
        {view === 'dashboard' && <Dashboard api={api} onNavigate={setView} user={user} />}
        {view === 'customers' && <Customers api={api} user={user} notify={setToast} />}
        {view === 'profile' && <Customer360 api={api} />}
        {view === 'loans' && <Loans api={api} notify={setToast} user={user} />}
        {view === 'collections' && <Collections api={api} user={user} notify={setToast} />}
        {view === 'planner' && <EmiPlanner />}
        {view === 'search' && <SearchView api={api} />}
        {view === 'reports' && <Reports api={api} />}
        {view === 'accounting' && <Accounting api={api} user={user} notify={setToast} />}
        {view === 'audit' && <Audit api={api} />}
        {view === 'settings' && <SettingsView api={api} notify={setToast} />}
        <button className="ai-fab" onClick={() => setAssistantOpen(true)} aria-label="Open Sakthi AI assistant"><Sparkles size={21} /><span>Ask Sakthi AI</span></button>
        {assistantOpen && <AiAssistant api={api} onClose={() => setAssistantOpen(false)} />}
      </main>
    </div>
  );
}

function viewTitle(view, t) {
  return {
    dashboard: 'Today at a glance',
    customers: 'Customer onboarding',
    profile: 'Customer 360 profile',
    loans: 'Loan management',
    collections: 'Collection entry',
    planner: 'Loan & EMI planner',
    search: 'Search and filters',
    reports: 'Financial reports',
    accounting: 'Accounting & reconciliation',
    audit: 'Security audit log',
    settings: 'Owner settings'
  }[view] || t.dashboard;
}

function Login({ t, setUser, api, theme, setTheme, lang, setLang }) {
  const [username, setUsername] = useState(IS_DEMO ? 'owner' : '');
  const [password, setPassword] = useState(IS_DEMO ? 'owner123' : '');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const accounts = [
    ['owner', 'owner123', 'Owner full access'],
    ['manager', 'manager123', 'Customers, loans, reports'],
    ['collector', 'collector123', 'Collection entry only'],
    ['accountant', 'accountant123', 'Read-only reports']
  ];
  async function submit(e) {
    e.preventDefault();
    setError('');
    try {
      const data = await api('/api/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) });
      setUser(data.user);
    } catch (err) {
      setError(err.message);
    }
  }
  return (
    <div className="login-page">
      <section className="login-hero">
        <div className="brand large">
          <div className="brand-mark"><img src="/logo-mark.svg" alt="" /></div>
          <div>
            <strong>{t.title}</strong>
            <span>{t.subtitle}</span>
          </div>
        </div>
        <div className="login-kicker"><span /> Lending operations, made clear</div>
        <h1>Every customer. Every collection. One calm workspace.</h1>
        <p>Run your lending business with a clean view of customers, repayments, risk, field collections, reports, and compliance.</p>
        <div className="hero-grid">
          <Metric icon={LockKeyhole} label="Protected records" value="Aadhaar encrypted" />
          <Metric icon={Bell} label="Never miss a due date" value="Smart overdue alerts" />
          <Metric icon={AreaChart} label="One clear view" value="Four operating areas" />
        </div>
      </section>
      <form className="login-card" onSubmit={submit}>
        <div className="form-head">
          <h2>{t.login}</h2>
          <div className="mini-actions">
            <button type="button" className="icon-btn" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>{theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}</button>
            <button type="button" className="icon-btn" onClick={() => setLang(lang === 'en' ? 'ta' : 'en')}><Globe2 size={18} /></button>
          </div>
        </div>
        <label>Username<input required autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} /></label>
        <label>Password<div className="password-field"><input required autoComplete="current-password" type={showPassword ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} /><button type="button" className="password-toggle" aria-label={showPassword ? 'Hide password' : 'Show password'} aria-pressed={showPassword} onClick={() => setShowPassword(value => !value)}>{showPassword ? <EyeOff size={19}/> : <Eye size={19}/>}</button></div></label>
        {error && <div className="error">{error}</div>}
        <button className="primary">Enter secure workspace <ChevronRight size={18} /></button>
        {IS_DEMO && <div className="demo-accounts">
          {accounts.map(([u, p, desc]) => (
            <button type="button" key={u} onClick={() => { setUsername(u); setPassword(p); }}>
              <strong>{u}</strong><span>{desc}</span>
            </button>
          ))}
        </div>}
      </form>
    </div>
  );
}

function Dashboard({ api, onNavigate, user }) {
  const [data, setData] = useState(null);
  const [dueFilter, setDueFilter] = useState('All');
  useEffect(() => { api('/api/dashboard').then(setData); }, []);
  if (!data) return <Skeleton />;
  const totals = data.totals;
  const expectedCollection = Math.round(totals.monthly_collection + totals.outstanding * 0.06);
  const collectionRate = Math.min(100, Math.round((totals.monthly_collection / Math.max(expectedCollection, 1)) * 100));
  const visibleDues = (data.pending_dues || []).filter(d => dueFilter === 'All' || dueFilter === 'Overdue' ? (dueFilter === 'All' || d.overdue) : d.frequency === dueFilter);
  return (
    <div className="content-grid">
      <section className="welcome-strip">
        <div><span className="welcome-label">Portfolio pulse</span><h2>{collectionRate}% of this month’s target collected</h2><p>Your team has {totals.active_loans} active loans across {data.area_summary.length} service areas.</p></div>
        <div className="quick-actions">
          <button onClick={() => onNavigate('customers')}><Users size={17} /> New customer</button>
          <button onClick={() => onNavigate('collections')}><ReceiptIndianRupee size={17} /> Record payment</button>
          {['owner','manager','accountant'].includes(user.role) && <button onClick={() => onNavigate('accounting')}><WalletCards size={17} /> Open accounting</button>}
          <button onClick={() => onNavigate('planner')}><Calculator size={17} /> Plan a loan</button>
        </div>
      </section>
      <section className="kpi-row">
        <Kpi icon={ReceiptIndianRupee} label="Today's Collection" value={money(totals.today_collection)} tone="green" />
        <Kpi icon={CreditCard} label="Active Loans" value={totals.active_loans} />
        <Kpi icon={AlertTriangle} label="Overdue Loans" value={totals.overdue_loans} tone="red" />
        <Kpi icon={ShieldCheck} label="Pending Verification" value={totals.pending_verification} tone="amber" />
        <Kpi icon={BadgeIndianRupee} label="Outstanding" value={money(totals.outstanding)} tone="amber" />
        <Kpi icon={Target} label="Expected Collection" value={money(expectedCollection)} tone="blue" />
      </section>
      <section className="panel wide">
        <div className="panel-head"><h2>Collection trend</h2><span>Monthly cash received</span></div>
        <div className="finance-strip">
          <Metric icon={Users} label="Total customers" value={totals.customers} />
          <Metric icon={ReceiptIndianRupee} label="Monthly collection" value={money(totals.monthly_collection)} />
          <Metric icon={AlertTriangle} label="Pending collection" value={money(Math.max(expectedCollection - totals.monthly_collection, 0))} />
        </div>
        <BarChart data={data.cashflow} x="month" y="collection" />
      </section>
      <section className="panel">
        <div className="panel-head"><h2>Loan portfolio mix</h2><span>Daily, weekly and monthly plans</span></div>
        <Donut daily={data.split.daily} monthly={data.split.monthly} />
        <div className="locked-note">Weekly plans: {data.split.weekly || 0}</div>
      </section>
      <section className="panel full">
        <div className="panel-head"><h2>Pending dues</h2><span>Nearest due first across every client plan</span></div>
        <div className="segmented-control">{['All','Daily','Weekly','Monthly','Overdue'].map(option=><button key={option} className={dueFilter===option?'active':''} onClick={()=>setDueFilter(option)}>{option}</button>)}</div>
        <div className="table-scroll"><table><thead><tr><th>Due date</th><th>Client</th><th>Plan</th><th>Installment</th><th>Amount due</th><th>Plan balance</th><th>Status</th></tr></thead><tbody>{visibleDues.map(d=><tr key={`${d.loan_id}-${d.installment_number}`}><td>{date(d.next_due_date)}</td><td>{d.customer_name}<small>{d.customer_id} · {d.mobile}</small></td><td>{d.frequency}<small>{d.loan_id}</small></td><td>#{d.installment_number}</td><td>{money(d.amount_due)}</td><td>{money(d.plan_balance)}</td><td><Status value={d.overdue ? `Overdue ${d.days_overdue}d` : 'Upcoming'} /></td></tr>)}</tbody></table></div>
      </section>
      <section className="panel wide area-performance">
        <div className="panel-head"><h2>Area performance</h2><span>Customers, exposure, and today’s collection</span></div>
        <div className="table-scroll area-performance-scroll">
          <table>
            <thead><tr><th>Area</th><th>Customers</th><th>Daily / Weekly / Monthly</th><th>Disbursed</th><th>Outstanding</th><th>Today</th><th>This month</th></tr></thead>
            <tbody>{data.area_summary.map(a => <tr key={a.area}><td data-label="Area"><b>{a.area}</b><small>{a.name}</small></td><td data-label="Customers">{a.customers}</td><td data-label="Loan plans"><span className="frequency-counts"><b>{a.daily_loans}</b><small>Daily</small><b>{a.weekly_loans}</b><small>Weekly</small><b>{a.monthly_loans}</b><small>Monthly</small></span></td><td data-label="Disbursed">{money(a.total_disbursed)}</td><td data-label="Outstanding">{money(a.outstanding)}</td><td data-label="Today">{money(a.today_collection)}</td><td data-label="This month">{money(a.monthly_collection)}</td></tr>)}</tbody>
          </table>
        </div>
      </section>
      <section className="panel">
        <div className="panel-head"><h2>Collector performance</h2><span>Collection volume and receipt count</span></div>
        <div className="collector-grid">
          {data.collector_breakdown.map(c => <div className="collector-card" key={c.name}><span>{c.name}</span><b>{money(c.total)}</b><small>{c.count} receipts</small></div>)}
        </div>
      </section>
      <section className="panel">
        <div className="panel-head"><h2>Needs attention</h2><span>Priority overdue follow-ups</span></div>
        <div className="alert-list">
          {data.alerts.slice(0, 8).map(a => <div className="alert-item" key={a.id}><AlertTriangle size={16} /><div><strong>{a.urgency}</strong><span>{a.customer_name} · {a.loan_id} · {money(a.balance)}</span></div></div>)}
        </div>
      </section>
    </div>
  );
}

function Customers({ api, user, notify }) {
  const [rows, setRows] = useState([]);
  const [knownCustomers, setKnownCustomers] = useState([]);
  const [areas, setAreas] = useState([]);
  const [form, setForm] = useState({ name: '', father_name: '', mobile: '', aadhaar: '', address: '', area: 'KUN', guarantor: '', status: 'Pending Verification', aadhaar_consent_given: false, aadhaar_consent_purpose: 'Identity verification for loan application', aadhaar_consent_reference: '' });
  const [fullAadhaar, setFullAadhaar] = useState({});
  const [receipt, setReceipt] = useState(null);
  const [registrationMode, setRegistrationMode] = useState('aadhaar');
  const [customerQuery, setCustomerQuery] = useState('');
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);
  const [aadhaarRequests, setAadhaarRequests] = useState([]);
  const [providerStatus, setProviderStatus] = useState({ configured:false, provider:null });
  const [onboardingOtp, setOnboardingOtp] = useState({ customer_id:'', verification_id:'', otp:'', attempts_remaining:3, resends_remaining:3, masked_destination:'', verified_at:'' });
  const [otpBusy, setOtpBusy] = useState(false);
  const load = async (query = customerQuery) => {
    const boot = await api('/api/bootstrap');
    setAreas(boot.areas);
    const customerRows = await api(`/api/customers?q=${encodeURIComponent(query)}`);
    setRows(customerRows);
    if (!query.trim()) setKnownCustomers(customerRows);
    setAadhaarRequests(['owner','manager'].includes(user.role) ? await api('/api/aadhaar/access-requests') : []);
    if (['owner','manager'].includes(user.role)) setProviderStatus(await api('/api/aadhaar/provider-status'));
  };
  useEffect(() => { load(); }, []);
  useEffect(() => {
    const timer = setTimeout(() => load(customerQuery), 250);
    return () => clearTimeout(timer);
  }, [customerQuery]);
  const previousMatches = useMemo(() => {
    const name = form.name.trim().toLowerCase();
    const mobile = form.mobile.trim();
    if (name.length < 3 && mobile.length < 4) return [];
    return knownCustomers.filter(customer =>
      (mobile.length >= 4 && customer.mobile?.includes(mobile)) ||
      (name.length >= 3 && customer.name?.toLowerCase().includes(name))
    ).slice(0, 4);
  }, [knownCustomers, form.name, form.mobile]);
  function usePreviousCustomer(customer) {
    setForm(current => ({ ...current, name: customer.name || '', father_name: customer.father_name || '', mobile: customer.mobile || '', address: customer.address || '', area: customer.area || current.area, guarantor: customer.guarantor || '' }));
    setReceipt({ type: 'Existing Customer Selected', ack: customer.customer_id, customer });
    notify(`Loaded existing customer ${customer.customer_id}. Create another loan from the Loans page; no duplicate profile was created.`);
  }
  async function submit(e) {
    e.preventDefault();
    if (saving) return;
    setFormError('');
    if (form.mobile.length !== 10) return setFormError('Enter a valid 10-digit Indian mobile number.');
    if (registrationMode === 'aadhaar' && form.aadhaar.length !== 12) return setFormError('Aadhaar must contain exactly 12 digits.');
    if (registrationMode === 'aadhaar' && (!form.aadhaar_consent_given || form.aadhaar_consent_reference.trim().length < 3)) return setFormError('Record customer consent and its reference before continuing.');
    setSaving(true);
    try {
      const payload = { ...form, aadhaar: registrationMode === 'aadhaar' ? form.aadhaar : '' };
      const res = await api('/api/customers', { method: 'POST', body: JSON.stringify(payload) });
      setReceipt({ type: res.duplicate ? 'Verification Acknowledgement' : 'Registration Acknowledgement', ack: res.ack_no, customer: res.customer });
      if (!res.duplicate && registrationMode === 'aadhaar' && providerStatus.configured) {
        const otpResult = await api('/api/aadhaar/otp/start', { method:'POST', body:JSON.stringify({ customer_id:res.customer.customer_id, purpose:form.aadhaar_consent_purpose, consent_reference:form.aadhaar_consent_reference, proposed_disbursal_amount:0, owner_notes:'Automatic verification during customer onboarding' }) });
        setOnboardingOtp({ customer_id:res.customer.customer_id, otp:'', verified_at:'', ...otpResult });
        notify(`Customer saved. Aadhaar OTP sent to ${otpResult.masked_destination}.`);
      } else {
        notify(res.duplicate ? 'Existing customer found. Duplicate customer was not created.' : registrationMode === 'aadhaar' ? 'Customer saved pending automatic Aadhaar verification.' : 'Manual profile saved as Pending Verification.');
      }
      setForm(current => ({ ...current, name: '', father_name: '', mobile: '', aadhaar: '', address: '', guarantor: '', status: 'Pending Verification', aadhaar_consent_given: false, aadhaar_consent_reference: '' }));
      await load();
    } catch (err) {
      setFormError(err.message || 'Customer could not be registered. Please try again.');
    } finally {
      setSaving(false);
    }
  }
  async function verifyOnboardingOtp() {
    if (![4,6].includes(onboardingOtp.otp.length)) return setFormError('OTP must contain exactly 4 or 6 digits.');
    setOtpBusy(true); setFormError('');
    try {
      const result = await api('/api/aadhaar/otp/verify', {method:'POST',body:JSON.stringify({verification_id:onboardingOtp.verification_id,otp:onboardingOtp.otp})});
      setOnboardingOtp(current=>({...current,otp:'',verified_at:result.verified_at}));
      notify(`Aadhaar verified automatically at ${new Date(result.verified_at).toLocaleString('en-IN')}.`);
      await load();
    } catch(err) {
      const remaining=err.message.match(/(\d+) attempts? remaining/i);
      setOnboardingOtp(current=>({...current,otp:'',attempts_remaining:remaining?Number(remaining[1]):current.attempts_remaining}));
      setFormError(err.message);
    } finally { setOtpBusy(false); }
  }
  async function resendOnboardingOtp() {
    setOtpBusy(true); setFormError('');
    try { const result=await api('/api/aadhaar/otp/resend',{method:'POST',body:JSON.stringify({verification_id:onboardingOtp.verification_id})}); setOnboardingOtp(current=>({...current,...result,otp:''})); notify('A new Aadhaar OTP was sent.'); }
    catch(err){setFormError(err.message);} finally{setOtpBusy(false);}
  }
  async function verify(id, status) {
    await api(`/api/customers/${id}/verification`, { method: 'PATCH', body: JSON.stringify({ status, reason: `${status} from customer registry` }) });
    notify(`Verification status updated to ${status}.`);
    await load();
  }
  async function deleteCustomer(row) {
    if (!row.can_delete_profile) return setFormError('This customer cannot be deleted until every loan is completed and the balance is zero.');
    if (!window.confirm(`Delete the active profile for ${row.name} (${row.customer_id})? Loan, payment, receipt, ledger, and audit history will be retained.`)) return;
    const confirmation = window.prompt(`Type ${row.customer_id} to confirm:`);
    if (confirmation === null) return;
    const reason = window.prompt('Enter the deletion reason (minimum 5 characters):');
    if (!reason) return;
    try {
      await api(`/api/customers/${encodeURIComponent(row.customer_id)}`, { method: 'DELETE', body: JSON.stringify({ confirmation, reason }) });
      notify(`Customer ${row.customer_id} removed from the active registry. Financial history was retained.`);
      await load();
    } catch (err) { setFormError(err.message); }
  }
  async function unmask(id) {
    const purpose = window.prompt('Specific purpose for viewing Aadhaar:');
    if (!purpose) return;
    const caseReference = window.prompt('Case or ticket reference:');
    if (!caseReference) return;
    await api(`/api/customers/${id}/aadhaar-access-requests`, { method: 'POST', body: JSON.stringify({ purpose, case_reference: caseReference }) });
    notify('Access request submitted. A different owner must approve the one-time Aadhaar view.');
    await load();
  }
  async function decideAccess(id, decision) { await api(`/api/aadhaar/access-requests/${id}/decision`, {method:'POST',body:JSON.stringify({decision,comments:'Reviewed against case reference'})}); notify(`Aadhaar access ${decision.toLowerCase()}d.`); await load(); }
  async function viewApproved(r) { const result = await api(`/api/customers/${r.customer_id}/aadhaar?access_request_id=${encodeURIComponent(r.request_id)}`); setFullAadhaar(current=>({...current,[r.customer_id]:result.aadhaar})); window.setTimeout(()=>setFullAadhaar(current=>({...current,[r.customer_id]:undefined})),15000); await load(); }
  return (
    <div className="split-layout">
      <form className="panel form-panel" onSubmit={submit}>
        <div className="panel-head"><div><span className="section-kicker">Secure onboarding</span><h2>Register a customer</h2></div><ShieldCheck size={22} /></div>
        <div className="segmented-control"><button type="button" className={registrationMode === 'aadhaar' ? 'active' : ''} onClick={() => setRegistrationMode('aadhaar')}>Aadhaar registration</button><button type="button" className={registrationMode === 'manual' ? 'active' : ''} onClick={() => { setRegistrationMode('manual'); setForm({ ...form, aadhaar: '' }); }}>Manual registration</button></div>
        <p className="form-intro">{registrationMode === 'aadhaar' ? providerStatus.configured ? `Aadhaar is encrypted and ${providerStatus.provider} sends an OTP to the Aadhaar-linked mobile. The profile remains pending until that OTP succeeds.` : 'Automatic Aadhaar verification needs an authorised AUA/KUA provider. Until connected, Aadhaar remains pending; a normal SMS is not presented as UIDAI verification.' : 'Create the profile without Aadhaar. It remains Pending Verification until an Owner or Manager approves it.'}</p>
        <div className="two-col">
          <label>Name<input required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></label>
          <label>Father's name<input required value={form.father_name} onChange={e => setForm({ ...form, father_name: e.target.value })} /></label>
          <label>Mobile<input required inputMode="numeric" minLength="10" maxLength="10" pattern="[6-9][0-9]{9}" value={form.mobile} onChange={e => setForm({ ...form, mobile: e.target.value.replace(/\D/g, '') })} /></label>
          {registrationMode === 'aadhaar' && <><label>Aadhaar<input required inputMode="numeric" minLength="12" maxLength="12" pattern="[0-9]{12}" value={form.aadhaar} onChange={e => setForm({ ...form, aadhaar: e.target.value.replace(/\D/g, '') })} /></label><label>Purpose disclosed<input required minLength="5" value={form.aadhaar_consent_purpose} onChange={e=>setForm({...form,aadhaar_consent_purpose:e.target.value})}/></label><label>Consent reference<input required minLength="3" placeholder="Signed form / OTP reference" value={form.aadhaar_consent_reference} onChange={e=>setForm({...form,aadhaar_consent_reference:e.target.value})}/></label><label className="check-row"><input type="checkbox" checked={form.aadhaar_consent_given} onChange={e=>setForm({...form,aadhaar_consent_given:e.target.checked})}/> Customer gave informed consent for this disclosed purpose</label></>}
          <label>Area<select value={form.area} onChange={e => setForm({ ...form, area: e.target.value })}>{areas.map(a => <option key={a.code}>{a.code}</option>)}</select></label>
          <div className="locked-note"><ShieldCheck size={16} /> New customers are saved as Pending Verification until Owner/Manager approval.</div>
        </div>
        {previousMatches.length > 0 && <div className="customer-suggestions" role="listbox" aria-label="Existing customer suggestions"><strong>Existing customer found</strong><small>Select the previous profile instead of creating a duplicate.</small>{previousMatches.map(customer => <button type="button" key={customer.customer_id} onClick={() => usePreviousCustomer(customer)}><span>{customer.name}<small>{customer.customer_id} · {customer.mobile}</small></span><ChevronRight size={17}/></button>)}</div>}
        <label>Address<textarea required value={form.address} onChange={e => setForm({ ...form, address: e.target.value })} /></label>
        <label>Guarantor<input value={form.guarantor} onChange={e => setForm({ ...form, guarantor: e.target.value })} /></label>
        {formError && <div className="error" role="alert">{formError}</div>}
        <button className="primary" disabled={saving}><Plus size={18} /> {saving ? 'Saving securely…' : registrationMode === 'aadhaar' ? 'Register and send Aadhaar OTP' : 'Create pending profile'}</button>
        {onboardingOtp.verification_id && <div className="servicing-box"><h3>Aadhaar OTP verification</h3><p>Customer {onboardingOtp.customer_id} · sent to {onboardingOtp.masked_destination || 'Aadhaar-linked mobile'}</p>{onboardingOtp.verified_at ? <div className="locked-note"><CheckCircle2 size={16}/> Verified at {new Date(onboardingOtp.verified_at).toLocaleString('en-IN')} · proof {onboardingOtp.verification_id}</div> : <><label>4 or 6-digit OTP<input inputMode="numeric" autoComplete="one-time-code" minLength="4" maxLength="6" pattern="(?:[0-9]{4}|[0-9]{6})" value={onboardingOtp.otp} onChange={e=>setOnboardingOtp({...onboardingOtp,otp:e.target.value.replace(/\D/g,'').slice(0,6)})}/></label><div className="action-row"><button type="button" className="primary small" disabled={otpBusy || ![4,6].includes(onboardingOtp.otp.length)} onClick={verifyOnboardingOtp}>Verify OTP</button><button type="button" className="ghost small" disabled={otpBusy || onboardingOtp.resends_remaining===0} onClick={resendOnboardingOtp}>Resend</button></div><small>{onboardingOtp.attempts_remaining} attempts · {onboardingOtp.resends_remaining} resends remaining</small></>}</div>}
      </form>
      <section className="panel">
        <div className="panel-head"><h2>Customer registry</h2><span>{rows.length} matching profiles</span></div>
        <div className="toolbar">
          <div className="searchbox">
            <Search size={18} />
            <input
              value={customerQuery}
              onChange={e => setCustomerQuery(e.target.value)}
              placeholder="Search customer name, ID, mobile, Aadhaar last 4, or area..."
            />
          </div>
          {customerQuery && <button className="ghost" onClick={() => setCustomerQuery('')}>Clear</button>}
        </div>
        <div className="table-scroll">
          <table>
            <thead><tr><th>ID</th><th>Name</th><th>Aadhaar</th><th>Status</th><th>Risk</th><th>Area</th><th>Actions</th></tr></thead>
            <tbody>{rows.map(r => <tr key={r.customer_id}><td>{r.customer_id}</td><td><div className="table-person"><span>{r.name.split(' ').map(x => x[0]).join('').slice(0,2)}</span><div>{r.name}<small>{r.mobile}</small></div></div></td><td>{fullAadhaar[r.customer_id] || r.aadhaar_masked}{r.aadhaar_verified_at && <small>Verified {date(r.aadhaar_verified_at)}</small>}</td><td><Status value={r.status} /></td><td><Risk score={r.risk_score} /></td><td>{r.area}</td><td><div className="action-row">{['owner','manager'].includes(user.role) && <>{r.has_aadhaar && <button className="ghost" onClick={() => unmask(r.customer_id)}><Eye size={15} /> Unmask</button>}{(!r.has_aadhaar || !providerStatus.configured) && <button className="ghost" onClick={() => verify(r.customer_id, 'Manual Verification Approved')}><CheckCircle2 size={15} /> Approve manually</button>}<button className="ghost danger" onClick={() => verify(r.customer_id, 'Verification Failed')}><AlertTriangle size={15} /> Fail</button></>}{user.role === 'owner' && r.can_delete_profile && <button className="ghost danger" onClick={() => deleteCustomer(r)}><X size={15} /> Delete completed</button>}</div></td></tr>)}</tbody>
          </table>
        </div>
      </section>
      {['owner','manager'].includes(user.role) && <section className="panel full">
        <div className="panel-head"><h2>Aadhaar access control</h2><span>Purpose-bound, independently approved, one-time views</span></div>
        <div className="table-scroll"><table><thead><tr><th>Request</th><th>Customer</th><th>Purpose</th><th>Requester</th><th>Status</th><th>Action</th></tr></thead><tbody>{aadhaarRequests.map(r=><tr key={r.request_id}><td>{r.request_id}<small>{r.case_reference}</small></td><td>{r.customer_id}</td><td>{r.purpose}</td><td>{r.requested_by}</td><td>{r.status}</td><td>{r.status==='Pending' && user.role==='owner' && r.requested_by_id!==user.id ? <div className="action-row"><button className="primary small" onClick={()=>decideAccess(r.request_id,'Approve')}>Approve</button><button className="ghost danger" onClick={()=>decideAccess(r.request_id,'Reject')}>Reject</button></div> : r.status==='Approved' && r.requested_by_id===user.id && r.remaining_views>0 ? <button className="ghost" onClick={()=>viewApproved(r)}>One-time view</button> : '—'}</td></tr>)}</tbody></table></div>
      </section>}
      {receipt && <ReceiptModal title={receipt.type} onClose={() => setReceipt(null)} data={receipt} />}
    </div>
  );
}

function Customer360({ api }) {
  const [customers, setCustomers] = useState([]);
  const [loans, setLoans] = useState([]);
  const [payments, setPayments] = useState([]);
  const [verificationEvents, setVerificationEvents] = useState([]);
  const [selectedId, setSelectedId] = useState('');

  useEffect(() => {
    async function load() {
      const cs = await api('/api/customers');
      const ls = await api('/api/loans');
      const ps = await api('/api/payments');
      const ve = await api('/api/verification-events');
      setCustomers(cs);
      setLoans(ls);
      setPayments(ps);
      setVerificationEvents(ve);
      setSelectedId(cs[0]?.customer_id || '');
    }
    load();
  }, []);

  const customer = customers.find(c => c.customer_id === selectedId) || customers[0];
  if (!customer) return <Skeleton />;
  const customerLoans = loans.filter(l => l.customer_id === customer.customer_id);
  const customerPayments = payments.filter(p => p.customer_id === customer.customer_id);
  const customerVerificationEvents = verificationEvents.filter(v => v.customer_id === customer.customer_id);
  const totals = customerLoans.reduce((acc, loan) => ({
    borrowed: acc.borrowed + loan.principal,
    paid: acc.paid + loan.paid,
    balance: acc.balance + loan.balance
  }), { borrowed: 0, paid: 0, balance: 0 });
  const timeline = [
    { time: customer.created_at, icon: Users, title: 'Customer Created', detail: `${customer.customer_id} registered with ${customer.status}` },
    ...customerLoans.map(loan => ({ time: loan.borrow_date, icon: CreditCard, title: 'Loan Issued', detail: `${loan.loan_id} for ${money(loan.principal)}` })),
    ...customerPayments.map(payment => ({ time: payment.timestamp, icon: ReceiptIndianRupee, title: 'Payment Received', detail: `${payment.receipt_no} for ${money(payment.amount)} via ${payment.mode}` })),
    ...customerVerificationEvents.map(event => ({ time: event.timestamp, icon: ShieldCheck, title: 'Verification Done', detail: event.verification_id ? `${event.status} through ${event.provider} · proof ${event.verification_id}` : `${event.from_status || 'New'} to ${event.to_status || event.status} by ${event.user || event.updated_by}` }))
  ].sort((a, b) => new Date(b.time) - new Date(a.time));

  return (
    <div className="profile-layout">
      <section className="panel profile-card">
        <div className="avatar">{customer.name.split(' ').map(x => x[0]).slice(0, 2).join('')}</div>
        <h2>{customer.name}</h2>
        <p>{customer.customer_id} - {customer.area} - {customer.mobile}</p>
        <label>Customer<select value={customer.customer_id} onChange={e => setSelectedId(e.target.value)}>{customers.map(c => <option key={c.customer_id} value={c.customer_id}>{c.customer_id} - {c.name}</option>)}</select></label>
        <div className="profile-tags">
          <Status value={customer.status} />
          <span className="pill">Risk {customer.risk_score}</span>
          <span className="pill">Aadhaar {customer.aadhaar_masked}</span>
        </div>
        <div className="document-grid">
          {['Aadhaar', 'PAN', 'Agreement', 'Photo', 'Signature', 'Guarantor'].map(item => <div key={item}><FileText size={16} /><span>{item}</span><small>Version ready</small></div>)}
        </div>
      </section>

      <section className="panel wide">
        <div className="panel-head"><h2>Complete loan history</h2><span>Current loan, closed loans, outstanding, and collection history</span></div>
        <div className="finance-strip">
          <Metric icon={WalletCards} label="Total borrowed" value={money(totals.borrowed)} />
          <Metric icon={CheckCircle2} label="Total repaid" value={money(totals.paid)} />
          <Metric icon={BadgeIndianRupee} label="Outstanding" value={money(totals.balance)} />
        </div>
        <LoanTable rows={customerLoans} />
        <div className="locked-note">Completed plans are marked Closed and retained as financial history. They are never deleted. The same customer profile may simultaneously hold daily, weekly, and monthly plans.</div>
      </section>

      <section className="panel timeline-panel">
        <div className="panel-head"><h2>Customer timeline</h2><span>Chronological audit of customer, loan, payment, reminder, and document events</span></div>
        <div className="timeline">{timeline.map((item, idx) => <div className="timeline-item" key={`${item.title}-${idx}`}><item.icon size={16} /><div><strong>{item.title}</strong><span>{item.detail}</span><small>{date(item.time)}</small></div></div>)}</div>
      </section>

      <section className="panel">
        <div className="panel-head"><h2>AI risk intelligence</h2><span>Duplicate, fraud, and collection-score signals</span></div>
        <div className="score-ring" style={{ '--score': `${customer.risk_score}%` }}><span>{customer.risk_score}</span></div>
        <div className="insight-list">
          <span><SearchCheck size={15} /> Duplicate detection by Aadhaar, mobile, and customer ID</span>
          <span><Bell size={15} /> Reminder history and follow-up queue</span>
          <span><Sparkles size={15} /> Natural language search ready</span>
        </div>
      </section>
    </div>
  );
}

function Loans({ api, notify, user }) {
  const [rows, setRows] = useState([]);
  const [boot, setBoot] = useState({ collectors: [], loan_types: [] });
  const [customers, setCustomers] = useState([]);
  const [form, setForm] = useState({ customer_id: '', principal: 50000, interest_rate: 2.14, loan_type: 'Daily 100-Day', repayment_period: 100, collector_id: '', disbursement_mode: 'Cash', interest_method: 'Reducing', processing_fee: 0, tax_rate: 18, first_due_date: '', moratorium_periods: 0, moratorium_interest_capitalized: true, preclosure_charge_rate: 0, late_fee: 0, kfs_acknowledgement_reference: '', identity_verification_id: null });
  const [providerStatus, setProviderStatus] = useState({ configured:false, verified_disbursal_required:false });
  const [identity, setIdentity] = useState({ purpose:'Identity verification before loan disbursal', consent_reference:'', owner_notes:'', verification_id:'', otp:'', attempts_remaining:3, resends_remaining:3, expires_at:'', resend_available_at:'' });
  const [identityError, setIdentityError] = useState('');
  const [identityBusy, setIdentityBusy] = useState(false);
  const [quote, setQuote] = useState(null);
  const [loanError, setLoanError] = useState('');
  const [savingLoan, setSavingLoan] = useState(false);
  const [service, setService] = useState({ loan_id: '', amount: '', strategy: 'Reduce EMI', effective_date: new Date().toISOString().slice(0,10), consent: '', annual_rate: 12, periods: 12, moratorium: 0, approval: '', reason: '' });
  const load = async () => {
    const b = await api('/api/bootstrap');
    const cs = await api('/api/customers');
    if (['owner','manager'].includes(user.role)) setProviderStatus(await api('/api/aadhaar/provider-status'));
    setBoot(b);
    setCustomers(cs);
    const loanRows = await api('/api/loans');
    setRows(loanRows);
    setForm(f => ({ ...f, customer_id: f.customer_id || cs[0]?.customer_id || '', collector_id: f.collector_id || b.collectors[0]?.id || '' }));
    setService(s => ({ ...s, loan_id: s.loan_id || loanRows[0]?.loan_id || '' }));
  };
  useEffect(() => { load(); }, []);
  useEffect(() => { setQuote(null); }, [form]);
  async function submit(e) {
    e.preventDefault();
    setLoanError('');
    const body = { ...form, principal: Number(form.principal), interest_rate: Number(form.interest_rate), repayment_period: Number(form.repayment_period), processing_fee: Number(form.processing_fee), tax_rate: Number(form.tax_rate), moratorium_periods: Number(form.moratorium_periods), preclosure_charge_rate: Number(form.preclosure_charge_rate), late_fee: Number(form.late_fee), first_due_date: form.first_due_date || null };
    setSavingLoan(true);
    try {
      await api('/api/loans', { method: 'POST', body: JSON.stringify(body) });
      notify('Loan disbursed and acknowledgement ready.');
      setQuote(null);
      await load();
    } catch (err) {
      setLoanError(err.message || 'Loan could not be created.');
    } finally { setSavingLoan(false); }
  }
  async function preview() {
    setLoanError('');
    const body = { ...form, principal: Number(form.principal), interest_rate: Number(form.interest_rate), repayment_period: Number(form.repayment_period), processing_fee: Number(form.processing_fee), tax_rate: Number(form.tax_rate), moratorium_periods: Number(form.moratorium_periods), preclosure_charge_rate: Number(form.preclosure_charge_rate), late_fee: Number(form.late_fee), first_due_date: form.first_due_date || null };
    try { setQuote(await api('/api/loan-quotes', { method: 'POST', body: JSON.stringify(body) })); }
    catch (err) { setQuote(null); setLoanError(err.message || 'Loan preview could not be generated.'); }
  }
  async function servicePost(path, body, message) { await api(path, { method:'POST', body:JSON.stringify(body) }); notify(message); await load(); }
  async function startIdentityOtp() { setIdentityError(''); setIdentityBusy(true); try { const result=await api('/api/aadhaar/otp/start',{method:'POST',body:JSON.stringify({customer_id:form.customer_id,purpose:identity.purpose,consent_reference:identity.consent_reference,proposed_disbursal_amount:Number(form.principal),owner_notes:identity.owner_notes})}); setIdentity({...identity,...result,verification_id:result.verification_id,otp:''}); notify(`OTP sent to ${result.masked_destination}.`); } catch(err) { setIdentityError(err.message); } finally { setIdentityBusy(false); } }
  async function verifyIdentityOtp() { setIdentityError(''); setIdentityBusy(true); try { const result=await api('/api/aadhaar/otp/verify',{method:'POST',body:JSON.stringify({verification_id:identity.verification_id,otp:identity.otp})}); setForm({...form,identity_verification_id:result.verification_id}); setIdentity({...identity,otp:''}); notify('Automatic Aadhaar verification succeeded and was linked to this disbursal.'); } catch(err) { const match=err.message.match(/(\d+) attempts? remaining/i); setIdentity(current=>({...current,otp:'',attempts_remaining:match ? Number(match[1]) : current.attempts_remaining})); setIdentityError(err.message); } finally { setIdentityBusy(false); } }
  async function resendIdentityOtp() { setIdentityError(''); setIdentityBusy(true); try { const result=await api('/api/aadhaar/otp/resend',{method:'POST',body:JSON.stringify({verification_id:identity.verification_id})}); setIdentity(current=>({...current,...result,otp:''})); notify('A new OTP was sent.'); } catch(err) { setIdentityError(err.message); } finally { setIdentityBusy(false); } }
  return (
    <div className="split-layout">
      <form className="panel form-panel" onSubmit={submit}>
        <div className="panel-head"><h2>Loan disbursement</h2><span>Auto Loan ID, installment and completion date</span></div>
        <div className="locked-note">Automatic Aadhaar: {providerStatus.configured ? `${providerStatus.provider} connected` : 'Not configured — authorized AUA/KUA provider credentials required'}</div>
        <label>Customer<select value={form.customer_id} onChange={e => setForm({ ...form, customer_id: e.target.value })}>{customers.map(c => <option key={c.customer_id}>{c.customer_id}</option>)}</select></label>
        <div className="two-col">
          <label>Principal<input type="number" value={form.principal} onChange={e => setForm({ ...form, principal: e.target.value })} /></label>
          <label>Annual interest %<input type="number" value="2.14" readOnly aria-readonly="true" /><small>Approved fixed rate</small></label>
          <label>Loan type<select value={form.loan_type} onChange={e => setForm({ ...form, loan_type: e.target.value, repayment_period: e.target.value.includes('Daily') ? 100 : e.target.value === 'Weekly' ? 52 : 12 })}>{boot.loan_types.map(x => <option key={x}>{x}</option>)}</select></label>
          <label>Period<input type="number" value={form.repayment_period} onChange={e => setForm({ ...form, repayment_period: e.target.value })} /></label>
          <label>Interest method<select value={form.interest_method} onChange={e=>setForm({...form,interest_method:e.target.value})}><option>Reducing</option><option>Flat</option></select></label>
          <label>Processing fee<input type="number" min="0" step="0.01" value={form.processing_fee} onChange={e=>setForm({...form,processing_fee:e.target.value})}/></label>
          <label>Tax on fee %<input type="number" min="0" step="0.01" value={form.tax_rate} onChange={e=>setForm({...form,tax_rate:e.target.value})}/></label>
          <label>First due date<input type="date" value={form.first_due_date} onChange={e=>setForm({...form,first_due_date:e.target.value})}/></label>
          <label>Moratorium periods<input type="number" min="0" value={form.moratorium_periods} onChange={e=>setForm({...form,moratorium_periods:e.target.value})}/></label>
          <label>Late charge<input type="number" min="0" step="0.01" value={form.late_fee} onChange={e=>setForm({...form,late_fee:e.target.value})}/></label>
          <label>Pre-closure charge %<input type="number" min="0" step="0.01" value={form.preclosure_charge_rate} onChange={e=>setForm({...form,preclosure_charge_rate:e.target.value})}/></label>
        </div>
        <label>Collector<select value={form.collector_id} onChange={e => setForm({ ...form, collector_id: e.target.value })}>{boot.collectors.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
        <label>Disbursement account<select value={form.disbursement_mode} onChange={e => setForm({ ...form, disbursement_mode: e.target.value })}><option>Cash</option><option>UPI</option><option>Bank Transfer</option></select></label>
        <label>KFS borrower acknowledgement reference<input required value={form.kfs_acknowledgement_reference} onChange={e=>setForm({...form,kfs_acknowledgement_reference:e.target.value})} placeholder="Signed/OTP acknowledgement ID"/></label>
        {providerStatus.configured && <div className="servicing-box"><h3>Fresh Aadhaar OTP before money handover</h3><label>Purpose<input value={identity.purpose} onChange={e=>setIdentity({...identity,purpose:e.target.value})}/></label><label>Consent reference<input value={identity.consent_reference} onChange={e=>setIdentity({...identity,consent_reference:e.target.value})}/></label><label>Owner handover note<input value={identity.owner_notes} onChange={e=>setIdentity({...identity,owner_notes:e.target.value})}/></label><div className="action-row"><button type="button" className="ghost" disabled={identityBusy} onClick={startIdentityOtp}>{identityBusy ? 'Please wait…' : 'Send Aadhaar-linked OTP'}</button>{identity.verification_id && <><input inputMode="numeric" autoComplete="one-time-code" minLength="4" maxLength="6" pattern="(?:[0-9]{4}|[0-9]{6})" placeholder="4 or 6-digit OTP" value={identity.otp} onChange={e=>setIdentity({...identity,otp:e.target.value.replace(/\D/g,'').slice(0,6)})}/><button type="button" className="primary small" disabled={identityBusy || ![4,6].includes(identity.otp.length)} onClick={verifyIdentityOtp}>Verify OTP</button><button type="button" className="ghost small" disabled={identityBusy || identity.resends_remaining === 0} onClick={resendIdentityOtp}>Resend OTP</button></>}</div>{identity.verification_id && !form.identity_verification_id && <small>{identity.attempts_remaining} verification attempts · {identity.resends_remaining} resends remaining. OTPs expire automatically.</small>}{identityError && <div className="error-banner" role="alert">{identityError}</div>}{form.identity_verification_id && <small>Verified reference: {form.identity_verification_id}</small>}</div>}
        <button type="button" className="ghost" onClick={preview}><FileText size={18}/> Preview APR, KFS and schedule</button>
        {loanError && <div className="error" role="alert">{loanError}</div>}
        <button className="primary" disabled={!quote || savingLoan}><FileText size={18} /> {savingLoan ? 'Creating loan…' : 'Create loan after KFS acceptance'}</button>
        {quote && <div className="locked-note">APR {quote.apr}% · Net disbursed {money(quote.net_disbursed_amount)} · Instalment {money(quote.periodic_instalment)} · Total repayment {money(quote.total_repayment)}</div>}
      </form>
      <section className="panel">
        <div className="panel-head"><h2>Loan book</h2><span>Multiple daily, weekly and monthly plans per customer</span></div>
        <LoanTable rows={rows} />
        {rows.length > 0 && <div className="servicing-box">
          <h3>Controlled loan servicing</h3>
          <label>Loan<select value={service.loan_id} onChange={e=>setService({...service,loan_id:e.target.value})}>{rows.map(l=><option key={l.loan_id}>{l.loan_id}</option>)}</select></label>
          <div className="two-col"><label>Amount<input type="number" min="0.01" step="0.01" value={service.amount} onChange={e=>setService({...service,amount:e.target.value})}/></label><label>Effective date<input type="date" value={service.effective_date} onChange={e=>setService({...service,effective_date:e.target.value})}/></label></div>
          <label>Borrower consent / approval reference<input value={service.consent} onChange={e=>setService({...service,consent:e.target.value})}/></label>
          <div className="action-row"><select value={service.strategy} onChange={e=>setService({...service,strategy:e.target.value})}><option>Reduce EMI</option><option>Reduce Tenor</option></select><button className="ghost" onClick={()=>servicePost(`/api/loans/${service.loan_id}/part-payment`,{amount:Number(service.amount),strategy:service.strategy,effective_date:service.effective_date,borrower_consent_reference:service.consent,mode:'Bank Transfer'},'Part-payment posted and schedule version updated.')}>Part-payment</button><button className="ghost" onClick={()=>api(`/api/loans/${service.loan_id}/preclosure-quote`).then(q=>notify(`Pre-closure quote: ${money(q.total)}`))}>Pre-closure quote</button><button className="ghost" onClick={()=>api(`/api/loans/${service.loan_id}/kfs`).then(kfs=>downloadPdf(kfs,`KFS-${service.loan_id}`))}>KFS / schedule PDF</button></div>
          {user.role === 'owner' && <details><summary>Restructure or write-off</summary><div className="two-col"><label>New annual rate<input type="number" value={service.annual_rate} onChange={e=>setService({...service,annual_rate:e.target.value})}/></label><label>Remaining periods<input type="number" value={service.periods} onChange={e=>setService({...service,periods:e.target.value})}/></label><label>Moratorium periods<input type="number" value={service.moratorium} onChange={e=>setService({...service,moratorium:e.target.value})}/></label><label>Approval reference<input value={service.approval} onChange={e=>setService({...service,approval:e.target.value})}/></label></div><label>Reason<input value={service.reason} onChange={e=>setService({...service,reason:e.target.value})}/></label><div className="action-row"><button className="ghost" onClick={()=>servicePost(`/api/loans/${service.loan_id}/restructure`,{annual_rate:Number(service.annual_rate),remaining_periods:Number(service.periods),moratorium_periods:Number(service.moratorium),effective_date:service.effective_date,approval_reference:service.approval,borrower_consent_reference:service.consent},'Loan restructured with a new immutable schedule.')}>Restructure</button><button className="ghost danger" onClick={()=>servicePost(`/api/loans/${service.loan_id}/write-off`,{amount:Number(service.amount),reason:service.reason,approval_reference:service.approval},'Approved write-off posted to the ledger.')}>Write-off</button></div></details>}
        </div>}
      </section>
    </div>
  );
}

function Collections({ api, user, notify }) {
  const [loans, setLoans] = useState([]);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(null);
  const [amount, setAmount] = useState('');
  const [mode, setMode] = useState('Cash');
  const [receipt, setReceipt] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const load = async () => {
    const rows = await api('/api/loans');
    const collectible = rows.filter(row => row.balance > 0 && row.status !== 'Closed');
    setLoans(collectible);
    if (!selected && collectible[0]) setSelected(collectible[0]);
  };
  useEffect(() => { load(); }, []);
  const filtered = loans.filter(l => !query || `${l.loan_id} ${l.customer_id} ${l.customer_name}`.toLowerCase().includes(query.toLowerCase()));
  async function submit(e) {
    e.preventDefault();
    if (!selected || saving) return;
    setSaving(true);
    setError('');
    const requestId = crypto.randomUUID();
    try {
      const res = await api('/api/payments', {
        method: 'POST',
        headers: { 'Idempotency-Key': requestId },
        body: JSON.stringify({ loan_id: selected.loan_id, amount: Number(amount), mode, request_id: requestId })
      });
      setReceipt(res.receipt);
      setAmount('');
      notify('Payment saved safely. Receipt generated.');
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }
  return (
    <div className="collection-layout">
      <section className="panel loan-picker">
        <div className="panel-head"><h2>Find loan</h2><span>Loan ID or Customer ID</span></div>
        <div className="searchbox"><Search size={18} /><input placeholder="Search loan..." value={query} onChange={e => setQuery(e.target.value)} /></div>
        <div className="loan-list">{filtered.slice(0, 16).map(l => <button key={l.loan_id} className={selected?.loan_id === l.loan_id ? 'loan-item selected' : 'loan-item'} onClick={() => { setSelected(l); setAmount(l.installment); }}><strong>{l.loan_id}</strong><span>{l.customer_name} · {money(l.balance)}</span></button>)}</div>
      </section>
      <form className="panel collection-card" onSubmit={submit}>
        <div className="panel-head"><h2>Collection entry</h2><span>Simple field workflow with locked server timestamp</span></div>
        {selected ? (
          <>
            <div className="summary-card">
              <strong>{selected.customer_name}</strong>
              <span>{selected.loan_id} · {selected.loan_type}</span>
              <div className="amount-line">{money(selected.balance)} <small>outstanding</small></div>
            </div>
            <div className="two-col">
              <label>Amount<input type="number" required value={amount} onChange={e => setAmount(e.target.value)} /></label>
              <label>Mode<select value={mode} onChange={e => setMode(e.target.value)}><option>Cash</option><option>UPI</option><option>Bank Transfer</option></select></label>
            </div>
            <div className="locked-note"><LockKeyhole size={16} /> Date/time is captured on the server and cannot be edited by staff.</div>
            {error && <div className="error" role="alert">{error}</div>}
            <button className="primary" disabled={saving}><ReceiptIndianRupee size={18} /> {saving ? 'Saving payment…' : 'Save payment and print receipt'}</button>
          </>
        ) : <p>No loans available.</p>}
      </form>
      {receipt && <ReceiptModal title="Payment Receipt" onClose={() => setReceipt(null)} data={receipt} />}
    </div>
  );
}

function SearchView({ api }) {
  const [q, setQ] = useState('');
  const [result, setResult] = useState({ customers: [], loans: [] });
  async function run() {
    setResult(await api(`/api/search?q=${encodeURIComponent(q)}`));
  }
  useEffect(() => { run(); }, []);
  return (
    <section className="panel full">
      <div className="panel-head"><h2>Universal search</h2><span>Customer ID, Loan ID, mobile, name, area, Aadhaar last 4</span></div>
      <div className="toolbar"><div className="searchbox"><Search size={18} /><input value={q} onChange={e => setQ(e.target.value)} onKeyDown={e => e.key === 'Enter' && run()} placeholder="Try KUN, mobile, customer name..." /></div><button className="primary small" onClick={run}>Search</button></div>
      <h3>Loans</h3><LoanTable rows={result.loans} />
      <h3>Customers</h3>
      <table><thead><tr><th>ID</th><th>Name</th><th>Mobile</th><th>Aadhaar</th><th>Area</th><th>Risk</th></tr></thead><tbody>{result.customers.map(c => <tr key={c.customer_id}><td>{c.customer_id}</td><td>{c.name}</td><td>{c.mobile}</td><td>{c.aadhaar_masked}</td><td>{c.area}</td><td><Risk score={c.risk_score} /></td></tr>)}</tbody></table>
    </section>
  );
}

function Reports({ api }) {
  const [type, setType] = useState('daily-collection');
  const [customers, setCustomers] = useState([]);
  const [customerId, setCustomerId] = useState('');
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => { api('/api/customers').then(r => { setCustomers(r); setCustomerId(r[0]?.customer_id || ''); }); }, []);
  async function generate() {
    const body = { report_type: type, customer_id: customerId, date: new Date().toISOString().slice(0, 10), month: new Date().toISOString().slice(0, 7), year: new Date().getFullYear() };
    setLoading(true); setError('');
    try { setReport(await api('/api/reports', { method: 'POST', body: JSON.stringify(body) })); }
    catch (err) { setReport(null); setError(err.message); }
    finally { setLoading(false); }
  }
  useEffect(() => { if (type !== 'customer-ledger' || customerId) generate(); }, [type, customerId]);
  const filename = `${type}-${new Date().toISOString().slice(0, 10)}`;
  return (
    <div className="split-layout">
      <section className="panel form-panel">
        <div className="panel-head"><h2>Report center</h2><span>Generate, download, print, and share real business reports</span></div>
        <label>Report type<select value={type} onChange={e => setType(e.target.value)}><option value="customer-ledger">Customer Ledger</option><option value="daily-collection">Daily Collection</option><option value="monthly-cashflow">Monthly Cash Flow</option><option value="annual-report">Annual Report</option><option value="loan-summary">Loan Summary</option><option value="defaulters">Defaulters</option><option value="area-report">Area Performance</option><option value="collector-report">Collector Performance</option><option value="profit-report">Profit Report</option><option value="recovery-rate">Recovery Rate</option><option value="business-growth">Business Growth</option></select></label>
        {type === 'customer-ledger' && <label>Customer<select value={customerId} onChange={e => setCustomerId(e.target.value)}>{customers.length ? customers.map(c => <option key={c.customer_id}>{c.customer_id}</option>) : <option value="">No customers available</option>}</select></label>}
        <button className="primary" disabled={loading} onClick={generate}><FileBarChart2 size={18} /> {loading ? 'Generating…' : 'Generate report'}</button>
        {error && <div className="error-banner" role="alert">Report failed: {error}. No incomplete file was generated.</div>}
        <div className="export-grid">
          <button className="ghost" disabled={!report} onClick={() => downloadCsv(report, filename)}><Download size={16} /> CSV</button>
          <button className="ghost" disabled={!report} onClick={() => downloadExcel(report, filename)}><FileText size={16} /> Excel</button>
          <button className="ghost" disabled={!report} onClick={() => downloadPdf(report, filename)}><FileBarChart2 size={16} /> PDF</button>
          <button className="ghost" disabled={!report} onClick={() => window.print()}><Printer size={16} /> Print</button>
          <button className="ghost" disabled={!report} onClick={() => shareReport(report, filename)}><Globe2 size={16} /> Share</button>
          <a className={`ghost ${!report ? 'disabled' : ''}`} href={report ? `mailto:?subject=${encodeURIComponent(report.title)}&body=${encodeURIComponent(reportSummary(report))}` : undefined}><Bell size={16} /> Email</a>
        </div>
      </section>
      <section className="panel report-preview">
        <div className="receipt-paper">
          <h2>{report?.title || 'Report'}</h2>
          {loading ? <Skeleton /> : report ? <ReportTable report={report} /> : <p>Select a report and generate it.</p>}
        </div>
      </section>
    </div>
  );
}

function ReportTable({ report }) {
  const rows = reportRows(report);
  if (!rows.length) return <div className="locked-note">No records matched this report period.</div>;
  const headers = [...new Set(rows.flatMap(row => Object.keys(row)))];
  return <div className="table-wrap"><table><thead><tr>{headers.map(h=><th key={h}>{h.replaceAll('_',' ')}</th>)}</tr></thead><tbody>{rows.map((row,index)=><tr key={index}>{headers.map(h=><td key={h}>{typeof row[h] === 'object' ? JSON.stringify(row[h]) : String(row[h] ?? '')}</td>)}</tr>)}</tbody></table></div>;
}

function Accounting({ api, user, notify }) {
  const [summary, setSummary] = useState(null);
  const [journals, setJournals] = useState([]);
  const [reversalRequests, setReversalRequests] = useState([]);
  const [collectors, setCollectors] = useState([]);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [posting, setPosting] = useState('');
  const [expense, setExpense] = useState({ amount: '', description: '', paid_from: 'Cash', expense_category: 'General' });
  const [deposit, setDeposit] = useState({ collector_id: '', amount: '', destination: 'Cash', reference: '' });
  const [settlement, setSettlement] = useState({ amount: '', reference: '' });
  const [closing, setClosing] = useState({ business_date: new Date().toISOString().slice(0, 10), actual_cash: '', notes: '' });
  const [reversal, setReversal] = useState({ receipt_no: '', reason: '' });
  const [opening, setOpening] = useState({ account: 'Cash', amount: '', as_of_date: new Date().toISOString().slice(0, 10), reference: '' });
  const [adjustment, setAdjustment] = useState({ loan_id: '', kind: 'Penalty', amount: '', reason: '' });
  async function load() {
    setLoading(true);
    const [summaryResult, journalsResult, reversalsResult, bootResult] = await Promise.allSettled([
      api('/api/accounting/summary'), api('/api/accounting/journals?limit=100'), api('/api/accounting/reversal-requests'), api('/api/bootstrap')
    ]);
    const failures = [summaryResult,journalsResult,reversalsResult,bootResult].filter(result=>result.status==='rejected');
    if (summaryResult.status === 'fulfilled') setSummary(summaryResult.value);
    if (journalsResult.status === 'fulfilled') setJournals(journalsResult.value || []);
    if (reversalsResult.status === 'fulfilled') setReversalRequests(reversalsResult.value || []);
    if (bootResult.status === 'fulfilled') {
      const boot=bootResult.value; setCollectors(boot.collectors || []);
      setDeposit(current => ({ ...current, collector_id: current.collector_id || boot.collectors?.[0]?.id || '' }));
    }
    setError(failures.length ? `Some accounting data could not load: ${failures.map(result=>result.reason?.message || 'request failed').join('; ')}` : '');
    setLoading(false);
  }
  useEffect(() => { load().catch(err => setError(err.message)); }, []);
  useEffect(() => {
    if (!summary) return;
    const locked = summary.locked_opening_accounts || [];
    if (locked.includes(opening.account)) {
      const available = ['Cash', 'Bank Transfer', 'UPI'].find(account => !locked.includes(account));
      if (available) setOpening(current => ({ ...current, account: available }));
    }
  }, [summary]);
  function submitChecked(event, path, validationMessage, payload, message) {
    event.preventDefault();
    if (validationMessage) {
      setError(validationMessage);
      setActionError({ path, message: validationMessage });
      return;
    }
    post(path, payload, message);
  }
  async function post(path, payload, message) {
    if (posting) return;
    setError('');
    setActionError(null);
    setPosting(path);
    try {
      await api(path, { method: 'POST', body: JSON.stringify(payload) });
      notify(message); await load();
    } catch (err) { setError(err.message); setActionError({ path, message: err.message }); }
    finally { setPosting(''); }
  }
  if (loading && !summary) return <Skeleton />;
  if (!summary) return <section className="panel"><div className="error" role="alert">{error || 'Accounting data could not be loaded.'}</div><button className="primary" onClick={load}>Retry accounting</button></section>;
  return (
    <div className="content-grid accounting-page">
      <section className="kpi-row accounting-kpis">
        <Kpi icon={WalletCards} label="Cash on hand" value={money(summary.cash_on_hand)} />
        <Kpi icon={Users} label="With collectors" value={money(summary.cash_with_collectors)} tone="amber" />
        <Kpi icon={ReceiptIndianRupee} label="UPI unsettled" value={money(summary.upi_unsettled)} tone="blue" />
        <Kpi icon={BadgeIndianRupee} label="Bank ledger" value={money(summary.bank_balance)} tone="green" />
        <Kpi icon={CreditCard} label="Receivables" value={money(summary.receivables)} />
      </section>
      {error && <div className="error" role="alert">{error}</div>}
      {!journals.length && <div className="locked-note">No opening balance or financial journal exists yet. The owner must post verified opening balances first; expenses, settlements, and collector deposits cannot be posted against money that is not recorded in the ledger.</div>}
      {user.role === 'owner' && summary.cash_on_hand <= 0 && summary.bank_balance <= 0 && summary.upi_unsettled <= 0 && <div className="locked-note"><ShieldCheck size={17} /> <span><b>Start here:</b> record the verified Cash or Bank opening balance below. Until funds exist in the ledger, expenses and settlements are intentionally blocked.</span></div>}
      <section className="panel full">
        <div className="panel-head"><h2>Trial balance</h2><span>{summary.balanced ? 'Debits and credits are balanced' : 'Accounting imbalance detected — stop posting and investigate'}</span></div>
        <div className="table-scroll"><table><thead><tr><th>Code</th><th>Account</th><th>Type</th><th>Balance</th></tr></thead><tbody>{summary.accounts.map(account=><tr key={account.code}><td>{account.code}</td><td>{account.name}</td><td>{account.type}</td><td>{money(account.balance)}</td></tr>)}</tbody></table></div>
      </section>
      {user.role === 'owner' && <section className="panel accounting-actions accounting-setup">
        <div className="panel-head"><h2>1. Set up ledger funds</h2><span>Required before spending or settlement</span></div>
        <form noValidate onSubmit={e => submitChecked(e, '/api/accounting/opening-balances', Number(opening.amount)<=0 ? 'Enter a verified opening amount greater than ₹0.' : opening.reference.trim().length<3 ? 'Enter a statement or cash-count reference of at least 3 characters.' : '', { ...opening, amount: Number(opening.amount), request_id: crypto.randomUUID() }, 'Opening balance locked and posted.')}><h3>Opening balance</h3><select value={opening.account} onChange={e=>setOpening({...opening,account:e.target.value})}>{['Cash','UPI','Bank Transfer'].map(account=><option key={account} disabled={(summary.locked_opening_accounts||[]).includes(account)}>{account}{(summary.locked_opening_accounts||[]).includes(account)?' — already locked':''}</option>)}</select><input type="number" min="0.01" step="0.01" placeholder="Verified opening amount" value={opening.amount} onChange={e=>setOpening({...opening,amount:e.target.value})}/><input type="date" value={opening.as_of_date} onChange={e=>setOpening({...opening,as_of_date:e.target.value})}/><input placeholder="Statement or cash-count reference" value={opening.reference} onChange={e=>setOpening({...opening,reference:e.target.value})}/><button className="primary small" disabled={Boolean(posting)||(summary.locked_opening_accounts||[]).length>=3}>{posting==='/api/accounting/opening-balances'?'Posting…':'Lock opening balance'}</button>{actionError?.path==='/api/accounting/opening-balances' && <small className="form-error">{actionError.message}</small>}<small>Use the amount verified from physical cash count or a bank/UPI statement. Accounts marked “already locked” cannot be initialized twice.</small></form>
      </section>}
      {['owner','manager'].includes(user.role) && <section className="panel accounting-actions">
        <div className="panel-head"><h2>2. Post controlled transactions</h2><span>Every action creates a balanced, immutable journal</span></div>
        <form noValidate onSubmit={e => submitChecked(e, '/api/accounting/expenses', Number(expense.amount)<=0 ? 'Enter an expense amount greater than ₹0.' : expense.description.trim().length<3 ? 'Enter an expense description of at least 3 characters.' : '', { ...expense, amount: Number(expense.amount), request_id: crypto.randomUUID() }, 'Expense posted to the ledger.')}>
          <h3>Expense</h3><input type="number" min="0.01" step="0.01" placeholder="Amount" value={expense.amount} onChange={e => setExpense({...expense,amount:e.target.value})}/><input minLength="3" placeholder="Description" value={expense.description} onChange={e => setExpense({...expense,description:e.target.value})}/><select value={expense.paid_from} onChange={e => setExpense({...expense,paid_from:e.target.value})}><option>Cash</option><option>Bank Transfer</option></select><button className="primary small" disabled={Boolean(posting)}>{posting==='/api/accounting/expenses'?'Posting…':'Post expense'}</button>{(expense.paid_from==='Cash'?summary.cash_on_hand:summary.bank_balance)<=0 && <small className="form-warning">Unavailable until {expense.paid_from} has a positive ledger balance.</small>}{actionError?.path==='/api/accounting/expenses' && <small className="form-error">{actionError.message}</small>}
        </form>
        <form noValidate onSubmit={e => submitChecked(e, '/api/accounting/collector-deposits', !deposit.collector_id ? 'Select an active collector. No collectors are currently configured.' : Number(deposit.amount)<=0 ? 'Enter a deposit amount greater than ₹0.' : deposit.reference.trim().length<3 ? 'Enter a deposit reference of at least 3 characters.' : '', { ...deposit, amount: Number(deposit.amount), request_id: crypto.randomUUID() }, 'Collector cash deposit reconciled.')}>
          <h3>Collector deposit</h3><select value={deposit.collector_id} onChange={e => setDeposit({...deposit,collector_id:e.target.value})}><option value="">Select collector</option>{collectors.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select><input type="number" min="0.01" step="0.01" placeholder="Amount" value={deposit.amount} onChange={e => setDeposit({...deposit,amount:e.target.value})}/><input minLength="3" placeholder="Deposit reference" value={deposit.reference} onChange={e => setDeposit({...deposit,reference:e.target.value})}/><button className="primary small" disabled={Boolean(posting)}>{posting==='/api/accounting/collector-deposits'?'Posting…':'Confirm deposit'}</button>{!collectors.length ? <small className="form-warning">Unavailable: create an active Collector user first.</small> : summary.cash_with_collectors<=0 && <small className="form-warning">Unavailable until a Cash collection is assigned to a collector.</small>}{actionError?.path==='/api/accounting/collector-deposits' && <small className="form-error">{actionError.message}</small>}
        </form>
        <form noValidate onSubmit={e => submitChecked(e, '/api/accounting/upi-settlements', Number(settlement.amount)<=0 ? 'Enter a settlement amount greater than ₹0.' : settlement.reference.trim().length<3 ? 'Enter a bank reference of at least 3 characters.' : '', { ...settlement, amount: Number(settlement.amount), request_id: crypto.randomUUID() }, 'UPI settlement moved to the bank ledger.')}>
          <h3>UPI settlement</h3><input type="number" min="0.01" step="0.01" placeholder="Amount" value={settlement.amount} onChange={e => setSettlement({...settlement,amount:e.target.value})}/><input minLength="3" placeholder="Bank reference" value={settlement.reference} onChange={e => setSettlement({...settlement,reference:e.target.value})}/><button className="primary small" disabled={Boolean(posting)}>{posting==='/api/accounting/upi-settlements'?'Posting…':'Settle to bank'}</button>{summary.upi_unsettled<=0 && <small className="form-warning">Unavailable until a UPI collection creates an unsettled UPI balance.</small>}{actionError?.path==='/api/accounting/upi-settlements' && <small className="form-error">{actionError.message}</small>}
        </form>
        <form noValidate onSubmit={e => submitChecked(e, `/api/loans/${encodeURIComponent(adjustment.loan_id)}/adjustments`, !adjustment.loan_id.trim() ? 'Enter an existing Loan ID.' : Number(adjustment.amount)<=0 ? 'Enter an adjustment amount greater than ₹0.' : adjustment.reason.trim().length<5 ? 'Enter a mandatory reason of at least 5 characters.' : '', { kind: adjustment.kind, amount: Number(adjustment.amount), reason: adjustment.reason, request_id: crypto.randomUUID() }, 'Loan penalty or waiver posted.')}><h3>Penalty or waiver</h3><input placeholder="Loan ID" value={adjustment.loan_id} onChange={e=>setAdjustment({...adjustment,loan_id:e.target.value})}/><select value={adjustment.kind} onChange={e=>setAdjustment({...adjustment,kind:e.target.value})}><option>Penalty</option><option>Interest Waiver</option><option>Penalty Waiver</option></select><input type="number" min="0.01" step="0.01" placeholder="Amount" value={adjustment.amount} onChange={e=>setAdjustment({...adjustment,amount:e.target.value})}/><input minLength="5" placeholder="Mandatory reason" value={adjustment.reason} onChange={e=>setAdjustment({...adjustment,reason:e.target.value})}/><button className="primary small" disabled={Boolean(posting)}>{posting.includes('/adjustments')?'Posting…':'Post adjustment'}</button>{actionError?.path.includes('/adjustments') && <small className="form-error">{actionError.message}</small>}</form>
      </section>}
      {user.role === 'owner' && <section className="panel accounting-actions">
        <form noValidate onSubmit={e => submitChecked(e, '/api/accounting/daily-close', closing.actual_cash==='' || Number(closing.actual_cash)<0 ? 'Enter the actual physical cash counted, including ₹0 when no cash exists.' : '', { ...closing, actual_cash: Number(closing.actual_cash) }, 'Business day closed and variance recorded.')}><h3>Daily cash closing</h3><input type="date" value={closing.business_date} onChange={e=>setClosing({...closing,business_date:e.target.value})}/><input type="number" min="0" step="0.01" placeholder="Actual counted cash" value={closing.actual_cash} onChange={e=>setClosing({...closing,actual_cash:e.target.value})}/><input placeholder="Closing notes" value={closing.notes} onChange={e=>setClosing({...closing,notes:e.target.value})}/><button className="primary small" disabled={Boolean(posting)}>{posting==='/api/accounting/daily-close'?'Closing…':'Close business day'}</button>{actionError?.path==='/api/accounting/daily-close' && <small className="form-error">{actionError.message}</small>}</form>
        <form noValidate onSubmit={e => { const path=`/api/payments/${encodeURIComponent(reversal.receipt_no)}/reversal-requests`; submitChecked(e, path, !reversal.receipt_no.trim() ? 'Enter an existing receipt number.' : reversal.reason.trim().length<5 ? 'Enter a correction reason of at least 5 characters.' : '', { reason: reversal.reason }, 'Reversal request submitted. A different manager must approve it.'); }}><h3>Request receipt reversal</h3><input placeholder="Receipt number" value={reversal.receipt_no} onChange={e=>setReversal({...reversal,receipt_no:e.target.value})}/><input minLength="5" placeholder="Mandatory correction reason" value={reversal.reason} onChange={e=>setReversal({...reversal,reason:e.target.value})}/><button className="ghost danger" disabled={Boolean(posting)}>{posting.includes('/reversal-requests')?'Submitting…':'Submit for approval'}</button>{actionError?.path.includes('/reversal-requests') && <small className="form-error">{actionError.message}</small>}</form>
      </section>}
      <section className="panel full">
        <div className="panel-head"><h2>Reversal approvals</h2><span>Maker-checker: requester and approver must be different users</span></div>
        <div className="table-scroll"><table><thead><tr><th>Request</th><th>Original transaction</th><th>Reason</th><th>Maker</th><th>Status / checker</th><th>Decision</th></tr></thead><tbody>{reversalRequests.length ? reversalRequests.map(r=><tr key={r.request_id}><td>{r.request_id}<small>{date(r.requested_at)}</small></td><td>{r.original_entry_id}<small>{r.original_source_type}: {r.original_source_id}</small></td><td>{r.reason}</td><td>{r.requested_by}<small>{r.requested_by_role}</small></td><td>{r.status}<small>{r.decided_by || 'Awaiting independent checker'}</small></td><td>{r.status === 'Pending' && ['owner','manager'].includes(user.role) && r.requested_by_id !== user.id ? <div className="row-actions"><button className="primary small" onClick={()=>post(`/api/accounting/reversal-requests/${r.request_id}/decision`, {decision:'Approve',approval_reference:`APP-${Date.now()}`,comments:'Reviewed against original transaction'}, 'Reversal approved and counter-entry posted.')}>Approve</button><button className="ghost danger" onClick={()=>post(`/api/accounting/reversal-requests/${r.request_id}/decision`, {decision:'Reject',approval_reference:`REJ-${Date.now()}`,comments:'Rejected by checker'}, 'Reversal request rejected.')}>Reject</button></div> : r.requested_by_id === user.id && r.status === 'Pending' ? 'Independent checker required' : '—'}</td></tr>) : <tr><td colSpan="6">No reversal requests. Corrections will appear here after a receipt reversal is submitted.</td></tr>}</tbody></table></div>
      </section>
      <section className="panel full">
        <div className="panel-head"><h2>General journal</h2><span>{journals.length} latest balanced entries</span></div>
        <div className="table-scroll"><table><thead><tr><th>Entry</th><th>Time</th><th>Source</th><th>Description</th><th>Debit</th><th>Credit</th></tr></thead><tbody>{journals.length ? journals.map(j=><tr key={j.entry_id}><td>{j.entry_id}</td><td>{date(j.timestamp)}</td><td>{j.source_type}<small>{j.source_id}</small></td><td>{j.description}</td><td>{money(j.debit_paise/100)}</td><td>{money(j.credit_paise/100)}</td></tr>) : <tr><td colSpan="6">No journal entries yet. Post verified opening balances to begin accounting.</td></tr>}</tbody></table></div>
      </section>
    </div>
  );
}

function Audit({ api }) {
  const [rows, setRows] = useState([]);
  const [integrity, setIntegrity] = useState(null);
  useEffect(() => { Promise.all([api('/api/audit'),api('/api/audit/integrity')]).then(([log,check])=>{setRows(log);setIntegrity(check);}); }, []);
  return <section className="panel full"><div className="panel-head"><h2>Tamper-evident audit log</h2><span>{integrity?.current_epoch_valid ? `Current chain epoch verified: ${integrity.verified_entries} retained entries` : 'Current chain integrity failure'} · {integrity?.historical_integrity_incident ? 'Historical deletion incident preserved' : 'No historical incident'} · {integrity?.external_archive_configured ? 'External archive configured' : 'External WORM archive not configured'}</span></div><table><thead><tr><th>Sequence</th><th>Time</th><th>User</th><th>Action</th><th>Entity</th><th>IP</th></tr></thead><tbody>{rows.map(r => <tr key={r.id}><td>{r.chain_sequence || 'Legacy'}<small>{r.entry_hash?.slice(0,12)}</small></td><td>{date(r.timestamp)}</td><td>{r.user}<small>{r.role}</small></td><td>{r.action}</td><td>{r.entity}: {r.entity_id}</td><td>{r.ip}</td></tr>)}</tbody></table></section>;
}

function SettingsView({ api, notify }) {
  const [areas, setAreas] = useState([]);
  const [backups, setBackups] = useState([]);
  const [area, setArea] = useState({ code: '', name: '' });
  const load = async () => {
    setAreas((await api('/api/bootstrap')).areas);
    setBackups(await api('/api/backups'));
  };
  useEffect(() => { load(); }, []);
  async function addArea(e) {
    e.preventDefault();
    await api('/api/areas', { method: 'POST', body: JSON.stringify(area) });
    notify('New area added with independent customer counter.');
    setArea({ code: '', name: '' });
    load();
  }
  async function backup() {
    await api('/api/backups/manual', { method: 'POST', body: '{}' });
    notify('Manual backup completed and logged.');
    load();
  }
  return (
    <div className="split-layout">
      <form className="panel form-panel" onSubmit={addArea}>
        <div className="panel-head"><h2>Area management</h2><span>Add future branches without code changes</span></div>
        <div className="two-col"><label>Code<input maxLength="3" value={area.code} onChange={e => setArea({ ...area, code: e.target.value.toUpperCase() })} /></label><label>Name<input value={area.name} onChange={e => setArea({ ...area, name: e.target.value })} /></label></div>
        <button className="primary"><Plus size={18} /> Add area</button>
        <div className="pill-row">{areas.map(a => <span className="pill" key={a.code}>{a.code} · {a.name}</span>)}</div>
      </form>
      <section className="panel">
        <div className="panel-head"><h2>Backup control</h2><span>Nightly backup with 90-day retention, plus manual trigger</span></div>
        <button className="primary" onClick={backup}><DatabaseBackup size={18} /> Run manual backup</button>
        <table><thead><tr><th>ID</th><th>Timestamp</th><th>Status</th></tr></thead><tbody>{backups.map(b => <tr key={b.id}><td>{b.id}</td><td>{date(b.timestamp)}</td><td><CheckCircle2 size={16} /> {b.status}</td></tr>)}</tbody></table>
      </section>
    </div>
  );
}

function EmiPlanner() {
  const [principal, setPrincipal] = useState(250000);
  const rate = 2.14;
  const [months, setMonths] = useState(24);
  const monthlyRate = rate / 1200;
  const emi = monthlyRate ? principal * monthlyRate * Math.pow(1 + monthlyRate, months) / (Math.pow(1 + monthlyRate, months) - 1) : principal / months;
  const total = emi * months;
  return (
    <div className="planner-layout">
      <section className="panel planner-controls">
        <div className="panel-head"><div><span className="section-kicker">Instant estimate</span><h2>Build a comfortable repayment plan</h2></div><Calculator size={24} /></div>
        <label>Loan amount <strong>{money(principal)}</strong><input type="range" min="10000" max="2000000" step="10000" value={principal} onChange={e => setPrincipal(Number(e.target.value))} /></label>
        <label>Annual interest <strong>{rate}%</strong><input type="range" min="2.14" max="2.14" step="0.01" value={rate} readOnly aria-label="Approved annual interest rate 2.14 percent" /><small>Fixed approved rate</small></label>
        <label>Repayment tenure <strong>{months} months</strong><input type="range" min="3" max="60" value={months} onChange={e => setMonths(Number(e.target.value))} /></label>
        <div className="planner-note"><ShieldCheck size={18} /><span>This is an indicative reducing-balance estimate. Final terms should follow the approved sanction.</span></div>
      </section>
      <section className="planner-result">
        <span>Your estimated monthly payment</span><strong>{money(emi)}</strong><small>for {months} months</small>
        <div className="result-grid"><div><span>Principal</span><b>{money(principal)}</b></div><div><span>Total interest</span><b>{money(total - principal)}</b></div><div><span>Total payable</span><b>{money(total)}</b></div></div>
        <div className="repayment-bar"><i style={{ width: `${principal / total * 100}%` }} /></div>
        <div className="legend repayment-legend"><span><i className="dot success" />Principal</span><span><i className="dot accent" />Interest</span></div>
      </section>
    </div>
  );
}

function NotificationCenter({ api, onClose }) {
  const [items, setItems] = useState([]);
  useEffect(() => { api('/api/notifications').then(setItems).catch(() => setItems([])); }, []);
  return <div className="drawer-backdrop" onClick={onClose}><aside className="notification-drawer" onClick={e => e.stopPropagation()}><div className="drawer-head"><div><span className="section-kicker">Live operations</span><h2>Notification center</h2></div><button className="icon-btn" onClick={onClose}><X size={18} /></button></div>{items.length ? <div className="notification-list">{items.map(n => <div className="notification-item" key={n.id}><span className="notification-icon"><CalendarClock size={17} /></span><div><strong>{n.urgency || 'Repayment reminder'}</strong><p>{n.customer_name} · {n.loan_id}</p><small>{money(n.balance)} outstanding · {n.channel}</small></div></div>)}</div> : <div className="empty-state"><Bell size={28} /><h3>You’re all caught up</h3><p>New payment and overdue alerts will appear here.</p></div>}</aside></div>;
}

function AiAssistant({ api, onClose }) {
  const [messages, setMessages] = useState([{ role: 'ai', text: 'Vanakkam! I’m Sakthi AI. Ask me about collections, outstanding balances, overdue loans, customer dues, or the next action your team should take.' }]);
  const [query, setQuery] = useState('');
  const [busy, setBusy] = useState(false);
  const suggestions = ['How much is outstanding?', 'What did we collect today?', 'Show overdue risk', 'How much should KUN001 pay?'];
  async function ask(text = query) {
    if (!text.trim() || busy) return;
    setMessages(m => [...m, { role: 'user', text }]); setQuery(''); setBusy(true);
    try {
      const [dashboard, customers, loans, payments] = await Promise.all([api('/api/dashboard'), api('/api/customers'), api('/api/loans'), api('/api/payments')]);
      const lower = text.toLowerCase();
      let answer;
      const customerId = text.match(/\b[A-Z]{3}\d{3}\b/i)?.[0]?.toUpperCase();
      if (customerId) {
        const result = await api(`/api/search?q=${encodeURIComponent(customerId)}`);
        const loans = result.loans.filter(l => l.customer_id === customerId && l.status !== 'Closed');
        const due = loans.reduce((sum, l) => sum + Number(l.balance || 0), 0);
        const installment = loans.reduce((sum, l) => sum + Number(l.installment || 0), 0);
        answer = loans.length ? `${customerId} has ${loans.length} active loan${loans.length > 1 ? 's' : ''}, ${money(due)} total outstanding, and scheduled payments of about ${money(installment)}. Open Customer 360 before collecting to confirm the latest ledger.` : `I couldn’t find an active loan for ${customerId}. Try the customer name, mobile number, or check the global search.`;
      } else if (lower.includes('best collector') || lower.includes('top collector')) {
        const best = [...dashboard.collector_breakdown].sort((a,b) => b.total - a.total)[0];
        answer = best ? `${best.name} is currently the top collector with ${money(best.total)} across ${best.count} receipts.` : 'No collector receipts are available yet.';
      } else if (lower.includes('without aadhaar') || lower.includes('no aadhaar')) {
        const list = customers.filter(c => !c.has_aadhaar);
        answer = list.length ? `${list.length} customer${list.length > 1 ? 's are' : ' is'} without Aadhaar: ${list.slice(0,8).map(c => `${c.customer_id} ${c.name}`).join(', ')}${list.length > 8 ? ', and more.' : '.'}` : 'Every customer currently has Aadhaar on file.';
      } else if (lower.includes('multiple loan')) {
        const counts = loans.filter(l => l.status !== 'Closed').reduce((acc,l) => ({...acc,[l.customer_id]:(acc[l.customer_id]||0)+1}),{});
        const ids = Object.entries(counts).filter(([,count]) => count > 1).map(([id,count]) => `${id} (${count})`);
        answer = ids.length ? `Customers with multiple active loans: ${ids.join(', ')}.` : 'No customer currently has more than one active loan.';
      } else if (lower.includes('salem') || lower.includes('slm')) {
        const list = customers.filter(c => c.area === 'SLM');
        answer = `${list.length} Salem customers found: ${list.slice(0,8).map(c => `${c.customer_id} ${c.name}`).join(', ')}${list.length > 8 ? ', and more.' : '.'}`;
      } else if (lower.match(/(?:owing|above|more than).*50[,.]?000/)) {
        const grouped = loans.filter(l => l.status !== 'Closed').reduce((acc,l) => ({...acc,[l.customer_id]:(acc[l.customer_id]||0)+Number(l.balance||0)}),{});
        const list = Object.entries(grouped).filter(([,due]) => due > 50000).sort((a,b) => b[1]-a[1]);
        answer = list.length ? `${list.length} customers owe more than ₹50,000: ${list.slice(0,8).map(([id,due]) => `${id} ${money(due)}`).join(', ')}.` : 'No customer currently owes more than ₹50,000.';
      } else if (lower.includes('payment') && lower.match(/10[,.]?000|ten thousand/)) {
        const list = payments.filter(p => Number(p.amount) > 10000);
        answer = `${list.length} payments above ₹10,000 found${list.length ? `: ${list.slice(0,6).map(p => `${p.receipt_no} ${money(p.amount)}`).join(', ')}.` : '.'}`;
      } else if (lower.includes('profit') || lower.includes('interest income')) {
        const projected = loans.reduce((sum,l) => sum + Number(l.principal||0) * Number(l.interest_rate||0) / 100, 0);
        answer = `Projected portfolio interest is ${money(projected)}. For a period-specific realised figure, open Reports → Profit Report.`;
      } else if (lower.includes('cash balance') || lower.includes('cash in hand')) {
        const cash = payments.filter(p => p.mode === 'Cash').reduce((sum,p) => sum + Number(p.amount||0),0);
        answer = `Recorded cash collections total ${money(cash)}. Reconcile this with expenses and bank deposits before treating it as physical cash in hand.`;
      } else if (lower.includes('expected') || lower.includes('prediction') || lower.includes('forecast')) {
        const expected = Math.round(dashboard.totals.monthly_collection + dashboard.totals.outstanding * .06);
        answer = `The current expected collection is approximately ${money(expected)} based on recorded monthly collections and portfolio exposure. ${dashboard.totals.overdue_loans} overdue loans are the main forecast risk.`;
      } else if (lower.includes('area performance') || lower.includes('branch performance')) {
        const ranked = [...dashboard.area_summary].sort((a,b) => b.today_collection-a.today_collection);
        answer = `Area ranking by today’s collection: ${ranked.map(a => `${a.area} ${money(a.today_collection)}`).join(', ')}.`;
      } else if (lower.includes('today') || lower.includes('collect')) answer = `Today’s recorded collection is ${money(dashboard.totals.today_collection)}. This month is at ${money(dashboard.totals.monthly_collection)}.`;
      else if (lower.includes('overdue') || lower.includes('risk') || lower.includes('default')) answer = `${dashboard.totals.overdue_loans} loans are overdue. ${dashboard.alerts.length} priority reminders are queued. Start with the highest-balance cases in Needs attention.`;
      else if (lower.includes('outstanding') || lower.includes('pay') || lower.includes('due')) answer = `The current portfolio outstanding is ${money(dashboard.totals.outstanding)} across ${dashboard.totals.active_loans} active loans. Include a customer ID such as KUN001 for an exact borrower-level answer.`;
      else if (lower.includes('monthly report') || lower.includes('revenue growth')) answer = `This month’s recorded collection is ${money(dashboard.totals.monthly_collection)}. Open Reports → Business Growth for the downloadable month-by-month trend.`;
      else if (lower.includes('customer')) answer = `There are ${dashboard.totals.customers} customers, with ${dashboard.totals.pending_verification} waiting for verification. You can ask me about a specific customer using their ID.`;
      else answer = `Your portfolio has ${dashboard.totals.active_loans} active loans and ${money(dashboard.totals.outstanding)} outstanding. I can answer collection, overdue, customer due, and area-performance questions using live workspace data.`;
      setMessages(m => [...m, { role: 'ai', text: answer }]);
    } catch { setMessages(m => [...m, { role: 'ai', text: 'I could not reach the live portfolio data just now. Please retry in a moment.' }]); }
    finally { setBusy(false); }
  }
  return <div className="ai-panel"><div className="ai-head"><div className="ai-avatar"><Sparkles size={19} /></div><div><strong>Sakthi AI</strong><span><i /> Live portfolio assistant</span></div><button onClick={onClose}><X size={18} /></button></div><div className="ai-messages">{messages.map((m, i) => <div key={i} className={`ai-message ${m.role}`}>{m.text}</div>)}{busy && <div className="ai-message ai typing">Thinking through your portfolio…</div>}</div><div className="ai-suggestions">{suggestions.map(s => <button key={s} onClick={() => ask(s)}>{s}</button>)}</div><div className="ai-compose"><input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && ask()} placeholder="Ask about a customer or portfolio…" /><button onClick={() => ask()}><ChevronRight size={18} /></button></div></div>;
}

function CommandPalette({ onSelect, onClose }) {
  const actions = [
    ['dashboard', 'Open dashboard', LayoutDashboard],
    ['customers', 'Register customer', Users],
    ['profile', 'Open Customer 360', ContactRound],
    ['loans', 'Create loan', CreditCard],
    ['collections', 'Collect payment', ReceiptIndianRupee],
    ['planner', 'Plan EMI and affordability', Calculator],
    ['search', 'Global search', Search],
    ['reports', 'Generate reports', FileBarChart2],
    ['audit', 'Security audit', ShieldCheck],
    ['settings', 'Owner settings', Settings]
  ];
  const [q, setQ] = useState('');
  const filtered = actions.filter(([, label]) => label.toLowerCase().includes(q.toLowerCase()));
  return (
    <div className="modal-backdrop">
      <div className="command-modal">
        <div className="searchbox command-input"><Search size={18} /><input autoFocus value={q} onChange={e => setQ(e.target.value)} placeholder="Search commands, pages, reports..." /></div>
        <div className="command-list">
          {filtered.map(([id, label, Icon]) => <button key={id} onClick={() => onSelect(id)}><Icon size={17} /><span>{label}</span><ChevronRight size={15} /></button>)}
        </div>
        <button className="ghost" onClick={onClose}>Close</button>
      </div>
    </div>
  );
}

function LoanTable({ rows }) {
  return <div className="table-scroll"><table><thead><tr><th>Loan</th><th>Customer</th><th>Scheme</th><th>Installment</th><th>Paid</th><th>Balance</th><th>Status</th></tr></thead><tbody>{rows.map(l => <tr key={l.loan_id}><td>{l.loan_id}<small>{date(l.borrow_date)}</small></td><td>{l.customer_name || l.customer_id}<small>{l.area}</small></td><td>{l.loan_type}</td><td>{money(l.installment)}</td><td>{money(l.paid)}</td><td>{money(l.balance)}</td><td><Status value={l.status} /></td></tr>)}</tbody></table></div>;
}

function ReceiptModal({ title, data, onClose }) {
  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div className="panel-head"><h2>{title}</h2><button className="icon-btn" onClick={onClose}>×</button></div>
        <div className="receipt-paper">
          <h2>Sri Sakthi Thirumurugan Finance</h2>
          <p>{title}</p>
          <dl>
            <dt>Reference</dt><dd>{data.ack || data.receipt_no}</dd>
            <dt>Customer</dt><dd>{data.customer?.customer_id} · {data.customer?.name}</dd>
            <dt>Aadhaar</dt><dd>{data.customer?.aadhaar_masked}</dd>
            {data.loan && <><dt>Loan</dt><dd>{data.loan.loan_id} · {money(data.loan.balance)} balance</dd></>}
            {data.amount && <><dt>Amount</dt><dd>{money(data.amount)} via {data.mode}</dd></>}
            {data.collector && <><dt>Collector</dt><dd>{data.collector}</dd></>}
            <dt>Timestamp</dt><dd>{date(data.timestamp || new Date().toISOString())}</dd>
          </dl>
          <div className="signature-row"><span>Customer signature</span><span>Company seal</span></div>
        </div>
        <button className="primary" onClick={() => window.print()}><Printer size={18} /> Print / save PDF</button>
      </div>
    </div>
  );
}

function Kpi({ icon: Icon, label, value, tone = 'violet' }) {
  return <div className={`kpi ${tone}`}><Icon size={22} /><span>{label}</span><strong>{value}</strong></div>;
}

function Metric({ icon: Icon, label, value }) {
  return <div className="metric"><Icon size={22} /><span>{label}</span><strong>{value}</strong></div>;
}

function BarChart({ data, x, y }) {
  const max = Math.max(...data.map(d => d[y]), 1);
  return <div className="bar-chart">{data.map(d => <div className="bar-col" key={d[x]}><div className="bar" style={{ height: `${Math.max(8, d[y] / max * 100)}%` }}><span>{money(d[y])}</span></div><small>{d[x]}</small></div>)}</div>;
}

function Donut({ daily, monthly }) {
  const total = daily + monthly || 1;
  const angle = daily / total * 360;
  return <div className="donut-wrap"><div className="donut" style={{ background: `conic-gradient(var(--accent) 0 ${angle}deg, var(--success) ${angle}deg 360deg)` }}><span>{total}</span></div><div className="legend"><span><i className="dot accent" />Daily {daily}</span><span><i className="dot success" />Monthly {monthly}</span></div></div>;
}

function Risk({ score }) {
  const tone = score >= 75 ? 'good' : score >= 55 ? 'warn' : 'bad';
  return <span className={`risk ${tone}`}>{score || 60}</span>;
}

function Status({ value }) {
  return <span className={`status ${String(value).toLowerCase().replaceAll(' ', '-')}`}>{value}</span>;
}

function Skeleton() {
  return <div className="skeleton"><div /><div /><div /></div>;
}

function money(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value || 0);
}

function date(value) {
  if (!value) return '';
  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
}

function reportRows(report) {
  if (!report) return [];
  const arrays = Object.entries(report).filter(([, value]) => Array.isArray(value));
  if (arrays.length) return arrays.flatMap(([section, rows]) => rows.map(row => ({ section, ...(typeof row === 'object' ? row : { value: row }) })));
  return [Object.fromEntries(Object.entries(report).map(([k, v]) => [k, typeof v === 'object' ? JSON.stringify(v) : v]))];
}

function csvText(report) {
  const rows = reportRows(report);
  const headers = [...new Set(rows.flatMap(row => Object.keys(row)))];
  const escape = value => `"${String(value ?? '').replaceAll('"', '""')}"`;
  return '\ufeff' + [headers.map(escape).join(','), ...rows.map(row => headers.map(h => escape(row[h])).join(','))].join('\n');
}

function saveFile(content, name, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement('a'); a.href = url; a.download = name; a.style.display = 'none'; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function downloadCsv(report, filename) { saveFile(csvText(report), `${filename}.csv`, 'text/csv;charset=utf-8'); }

function downloadExcel(report, filename) {
  const rows = reportRows(report); const headers = [...new Set(rows.flatMap(row => Object.keys(row)))];
  const cell = value => String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
  const table = `<html><head><meta charset="utf-8"></head><body><h2>${cell(report.title || 'Report')}</h2><table border="1"><tr>${headers.map(h => `<th>${cell(h)}</th>`).join('')}</tr>${rows.map(row => `<tr>${headers.map(h => `<td>${cell(row[h])}</td>`).join('')}</tr>`).join('')}</table></body></html>`;
  saveFile(table, `${filename}.xls`, 'application/vnd.ms-excel');
}

function downloadPdf(report, filename) {
  const lines = [report.title || 'Business Report', `Generated: ${new Date().toLocaleString('en-IN')}`, '', ...JSON.stringify(report, null, 2).split('\n')].map(line => line.replace(/[^\x20-\x7E]/g, ' ').slice(0, 95));
  const pages = Array.from({length: Math.max(1, Math.ceil(lines.length / 48))}, (_, i) => lines.slice(i * 48, (i + 1) * 48));
  const fontRef = 3 + pages.length * 2;
  const pageRefs = pages.map((_, i) => 3 + i * 2);
  const objects = ['<< /Type /Catalog /Pages 2 0 R >>', `<< /Type /Pages /Kids [${pageRefs.map(ref=>`${ref} 0 R`).join(' ')}] /Count ${pages.length} >>`];
  pages.forEach((pageLines, i) => {
    const contentRef = 4 + i * 2;
    const stream = `BT\n/F1 9 Tf\n42 800 Td\n15 TL\n${pageLines.map((line, index) => `${index ? 'T*' : ''} (${line.replaceAll('\\', '\\\\').replaceAll('(', '\\(').replaceAll(')', '\\)')}) Tj`).join('\n')}\nET`;
    objects.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 ${fontRef} 0 R >> >> /Contents ${contentRef} 0 R >>`);
    objects.push(`<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`);
  });
  objects.push('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>');
  let pdf = '%PDF-1.4\n', offsets = [0]; objects.forEach((obj, i) => { offsets.push(pdf.length); pdf += `${i + 1} 0 obj\n${obj}\nendobj\n`; });
  const size = objects.length + 1;
  const xref = pdf.length; pdf += `xref\n0 ${size}\n0000000000 65535 f \n${offsets.slice(1).map(o => String(o).padStart(10, '0') + ' 00000 n ').join('\n')}\ntrailer << /Size ${size} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF`;
  saveFile(pdf, `${filename}.pdf`, 'application/pdf');
}

function reportSummary(report) { return `${report.title || 'Business report'}\n\n${JSON.stringify(report, null, 2).slice(0, 1800)}`; }
async function shareReport(report, filename) {
  const file = new File([csvText(report)], `${filename}.csv`, { type: 'text/csv' });
  if (navigator.share && (!navigator.canShare || navigator.canShare({ files: [file] }))) await navigator.share({ title: report.title, text: 'Finance report', files: [file] });
  else downloadCsv(report, filename);
}

createRoot(document.getElementById('root')).render(<App />);
