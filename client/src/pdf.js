// Readable PDF documents (reports, loan history, Key Facts Statement).
// jsPDF is loaded only when a PDF is downloaded, so the app itself stays small.

const BRAND = 'Sri Sakthi Thirumurugan Finance';
const ACCENT = [91, 33, 182];
const MUTED = [100, 100, 115];

// The built-in PDF font has no rupee symbol, so amounts are written as "Rs. 1,25,000".
const NUMBER = new Intl.NumberFormat('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
export const rs = value => (value === null || value === undefined || value === '' || Number.isNaN(Number(value)) ? '-' : `Rs. ${NUMBER.format(Number(value))}`);
const DAY = new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
const DAY_TIME = new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
const asDate = value => { const d = new Date(value); return Number.isNaN(d.getTime()) ? null : d; };
export const dayText = value => (value && asDate(value) ? DAY.format(asDate(value)) : '-');
export const dateTimeText = value => (value && asDate(value) ? DAY_TIME.format(asDate(value)) : '-');
// Keep to characters the built-in font can print.
const clean = value => String(value ?? '-').replace(/[–—]/g, '-').replace(/[‘’]/g, "'").replace(/[“”]/g, '"').replace(/₹/g, 'Rs.').replace(/[^\x20-\x7E -ÿ]/g, '');
const pretty = key => String(key).replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());

const MONEY_KEY = /(amount|total|balance|principal|paid|collect|disburs|outstanding|interest|installment|instalment|emi|profit|value|fee|due|debt|cash|repayment)/i;
const NOT_MONEY_KEY = /(count|rate|percent|days|number|installments_paid|remaining|period|customers|loans|_id$|date|^new_)/i;
const MONTH = new Intl.DateTimeFormat('en-IN', { month: 'long', year: 'numeric' });
function formatValue(key, value) {
  if (value === null || value === undefined || value === '') return '-';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'number') {
    if (/percent/i.test(key)) return `${NUMBER.format(value)}%`;
    if (MONEY_KEY.test(key) && !NOT_MONEY_KEY.test(key)) return rs(value);
    return NUMBER.format(value);
  }
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value)) return /(timestamp|_at$)/.test(key) ? dateTimeText(value) : dayText(value);
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)) return dayText(`${value}T00:00:00`);
  if (typeof value === 'string' && /^\d{4}-\d{2}$/.test(value)) return MONTH.format(new Date(`${value}-01T00:00:00`));
  if (Array.isArray(value)) return `${value.length} item${value.length === 1 ? '' : 's'}`;
  if (typeof value === 'object') return Object.entries(value).map(([k, v]) => `${pretty(k)}: ${formatValue(k, v)}`).join(', ');
  return String(value);
}

/**
 * doc = { title, subtitle?, sections: [ { heading, pairs: [[label, value], ...] }
 *                                      | { heading, columns: [header...], rows: [[...]], money?: [colIndex...] }
 *                                      | { heading, text } ], signatures?: [label...] }
 */
const LOGO_RATIO = 203 / 240; // width / height of /pdf-logo.jpg
let logoPromise;
// Loaded once per session; a PDF is still produced without the logo if it cannot be fetched.
function loadLogo() {
  logoPromise ||= fetch('/pdf-logo.jpg')
    .then(response => (response.ok ? response.blob() : null))
    .then(blob => blob && new Promise(resolve => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = () => resolve(null); reader.readAsDataURL(blob); }))
    .catch(() => null);
  return logoPromise;
}

export async function downloadPdfDocument(doc, filename) {
  const [{ jsPDF }, { autoTable }, logo] = await Promise.all([import('jspdf'), import('jspdf-autotable'), loadLogo()]);
  const wide = doc.sections.some(s => s.columns && s.columns.length > 7);
  const pdf = new jsPDF({ orientation: wide ? 'landscape' : 'portrait', unit: 'pt', format: 'a4' });
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 40;
  const generated = DAY_TIME.format(new Date());

  // Title block
  pdf.setFillColor(...ACCENT); pdf.rect(0, 0, pageWidth, 6, 'F');
  const logoHeight = 66;
  if (logo) pdf.addImage(logo, 'JPEG', margin, 16, logoHeight * LOGO_RATIO, logoHeight);
  const textX = logo ? margin + logoHeight * LOGO_RATIO + 14 : margin;
  pdf.setFont('helvetica', 'bold'); pdf.setFontSize(16); pdf.setTextColor(25, 25, 35);
  pdf.text(BRAND, textX, 38);
  pdf.setFontSize(13); pdf.setTextColor(...ACCENT);
  pdf.text(clean(doc.title), textX, 58);
  pdf.setFont('helvetica', 'normal'); pdf.setFontSize(9); pdf.setTextColor(...MUTED);
  pdf.text(clean(doc.subtitle ? `${doc.subtitle}   |   Generated ${generated}` : `Generated ${generated}`), textX, 74);
  pdf.setDrawColor(220, 220, 228); pdf.line(margin, 90, pageWidth - margin, 90);
  let y = 104;

  const ensureSpace = needed => { if (y + needed > pageHeight - 50) { pdf.addPage(); y = 50; } };
  const heading = text => {
    ensureSpace(40);
    pdf.setFont('helvetica', 'bold'); pdf.setFontSize(11); pdf.setTextColor(25, 25, 35);
    pdf.text(clean(text), margin, y + 4); y += 12;
  };

  for (const section of doc.sections) {
    if (section.pairs) {
      const pairs = section.pairs.filter(([, value]) => value !== undefined && value !== null && value !== '');
      if (!pairs.length) continue;
      if (section.heading) heading(section.heading);
      // Two label/value pairs per row keeps facts compact and easy to scan.
      const body = [];
      for (let i = 0; i < pairs.length; i += 2) body.push([clean(pairs[i][0]), clean(pairs[i][1]), clean(pairs[i + 1]?.[0] ?? ''), clean(pairs[i + 1]?.[1] ?? '')]);
      autoTable(pdf, {
        startY: y, margin: { left: margin, right: margin, top: 48 }, body, theme: 'grid',
        styles: { fontSize: 9.5, cellPadding: 5, lineColor: [230, 230, 236], lineWidth: 0.5, textColor: [30, 30, 40] },
        columnStyles: { 0: { fontStyle: 'bold', textColor: MUTED, cellWidth: 'auto', fillColor: [248, 247, 252] }, 2: { fontStyle: 'bold', textColor: MUTED, fillColor: [248, 247, 252] } },
      });
      y = pdf.lastAutoTable.finalY + 16;
    } else if (section.columns) {
      if (section.heading) heading(section.rows.length ? `${section.heading} (${section.rows.length})` : section.heading);
      if (!section.rows.length) {
        pdf.setFont('helvetica', 'italic'); pdf.setFontSize(9.5); pdf.setTextColor(...MUTED);
        pdf.text(clean(section.empty || 'No records.'), margin, y + 8); y += 24; continue;
      }
      const money = new Set(section.money || []);
      const columnStyles = Object.fromEntries([...money].map(index => [index, { halign: 'right' }]));
      autoTable(pdf, {
        startY: y, margin: { left: margin, right: margin, top: 48 }, head: [section.columns.map(clean)], body: section.rows.map(row => row.map(clean)),
        foot: section.footer ? [section.footer.map(clean)] : undefined, showFoot: 'lastPage', theme: 'striped',
        styles: { fontSize: 8.5, cellPadding: 4, overflow: 'linebreak', textColor: [30, 30, 40] },
        headStyles: { fillColor: ACCENT, textColor: 255, fontStyle: 'bold' },
        footStyles: { fillColor: [238, 235, 248], textColor: [25, 25, 35], fontStyle: 'bold' },
        alternateRowStyles: { fillColor: [247, 246, 251] }, columnStyles,
        didParseCell: data => { if ((data.section === 'head' || data.section === 'foot') && money.has(data.column.index)) data.cell.styles.halign = 'right'; },
      });
      y = pdf.lastAutoTable.finalY + 18;
    } else if (section.text) {
      if (section.heading) heading(section.heading);
      pdf.setFont('helvetica', 'normal'); pdf.setFontSize(9.5); pdf.setTextColor(50, 50, 60);
      const lines = pdf.splitTextToSize(clean(section.text), pageWidth - margin * 2);
      ensureSpace(lines.length * 13 + 8);
      pdf.text(lines, margin, y + 6); y += lines.length * 13 + 14;
    }
  }

  if (doc.signatures?.length) {
    ensureSpace(80); y += 40;
    const width = (pageWidth - margin * 2) / doc.signatures.length;
    doc.signatures.forEach((label, index) => {
      const x = margin + index * width;
      pdf.setDrawColor(150, 150, 160); pdf.line(x + 10, y, x + width - 20, y);
      pdf.setFont('helvetica', 'normal'); pdf.setFontSize(9); pdf.setTextColor(...MUTED);
      pdf.text(clean(label), x + 10, y + 14);
    });
  }

  const pages = pdf.getNumberOfPages();
  for (let page = 1; page <= pages; page++) {
    pdf.setPage(page);
    pdf.setFont('helvetica', 'normal'); pdf.setFontSize(8); pdf.setTextColor(...MUTED);
    if (logo && page > 1) pdf.addImage(logo, 'JPEG', margin, 12, 26 * LOGO_RATIO, 26);
    pdf.text(`${BRAND}  |  ${clean(doc.title)}`, margin, pageHeight - 22);
    pdf.text(`Page ${page} of ${pages}`, pageWidth - margin, pageHeight - 22, { align: 'right' });
  }
  pdf.save(`${filename}.pdf`);
}

const planName = type => (type === 'Daily 100-Day' ? 'Daily' : type === 'Weekly' ? 'Weekly' : type === 'Monthly EMI' ? 'Monthly' : type || '-');

// ---------- Key Facts Statement ----------
export function kfsDocument(kfs) {
  const ack = kfs.borrower_acknowledgement || {};
  const schedule = kfs.schedule || [];
  return {
    title: 'Key Facts Statement (KFS)',
    subtitle: `Loan ${kfs.loan_id}`,
    sections: [
      { heading: 'Borrower', pairs: [['Name', kfs.borrower?.name], ['Customer ID', kfs.borrower?.customer_id]] },
      { heading: 'Loan terms', pairs: [
        ['Loan amount (sanctioned)', rs(kfs.sanctioned_amount)], ['Cash handed over', rs(kfs.net_disbursed_amount)],
        ['Interest deducted upfront', rs(kfs.total_interest)], ['Monthly interest rate', `${kfs.monthly_interest_rate}%`],
        ['Annual Percentage Rate (APR)', kfs.apr ? `${NUMBER.format(kfs.apr)}%` : '-'], ['Processing fee', rs(kfs.processing_fee)],
        ['Repayment', `${rs(kfs.periodic_instalment)} x ${kfs.tenor_periods} ${String(kfs.repayment_frequency || '').toLowerCase()} instalments`], ['Total to repay', rs(kfs.total_repayment)],
        ['First instalment due', dayText(kfs.first_due_date)], ['Last instalment due', dayText(kfs.maturity_date)],
        ['Late charge (defaulters only)', kfs.late_fee ? rs(kfs.late_fee) : 'None'], ['Schedule version', kfs.schedule_version],
      ] },
      { heading: 'Borrower acknowledgement', pairs: ack.acknowledgement_no
        ? [['Acknowledgement no.', ack.acknowledgement_no], ['Confirmed by', `OTP on ${ack.mobile || 'registered mobile'}`], ['Confirmed at', dateTimeText(ack.verified_at)], ['Method', ack.method || 'OTP']]
        : [['Reference', ack.reference || 'Not recorded']] },
      { heading: 'Repayment schedule', columns: ['No.', 'Due date', 'Instalment', 'Balance before', 'Balance after'], money: [2, 3, 4],
        rows: schedule.filter(row => Number(row.payment) > 0).map(row => [row.number, dayText(row.due_date), rs(row.payment), rs(row.opening), rs(row.closing)]) },
      { heading: 'Important', text: `${kfs.disclaimer || ''} The APR shows the yearly cost of this loan including interest deducted before the cash is handed over. Please keep this statement for your records.` },
    ],
    signatures: ['Borrower signature', 'For ' + BRAND],
  };
}

// ---------- Complete loan history ----------
export function loanHistoryDocument(data) {
  const { loan = {}, customer = {}, schedule = [], payments = [], adjustments = [], events = [], part_payments: partPayments = [], writeoffs = [] } = data;
  const servicing = [...adjustments, ...events, ...partPayments, ...writeoffs]
    .sort((a, b) => new Date(a.timestamp || a.created_at) - new Date(b.timestamp || b.created_at));
  const legacy = !(loan.contract_version >= 2);
  return {
    title: 'Complete Loan History',
    subtitle: `Loan ${loan.loan_id} - ${customer.name || loan.customer_id}`,
    sections: [
      { heading: 'Borrower', pairs: [['Name', customer.name], ['Customer ID', customer.customer_id || loan.customer_id], ['Mobile', customer.mobile], ['Area', customer.area_name || customer.area]] },
      { heading: 'Loan', pairs: [
        ['Loan ID', loan.loan_id], ['Plan', planName(loan.loan_type)],
        ['Loan date', dayText(loan.borrow_date)], ['Last due date', dayText(loan.maturity_date || loan.expected_completion)],
        ['Loan amount', rs(loan.principal)], ['Cash handed over', rs(loan.net_disbursed ?? loan.principal)],
        [legacy ? 'Interest (in instalments)' : 'Interest deducted', rs(legacy ? Math.max(Number(loan.total_payable || 0) - Number(loan.principal || 0), 0) : loan.contract_interest)], ['Interest rate', `${loan.interest_rate}%${legacy ? '' : ' per month'}`],
        ['Instalment', rs(loan.installment)], ['Instalments left', loan.remaining_installments],
        ['Total paid', rs(loan.paid)], ['Outstanding', rs(loan.balance)],
        ['Status', loan.status], ['Existing loan entry', loan.existing_loan ? 'Yes (given before the app)' : 'No'],
      ] },
      { heading: 'Borrower acknowledgement', pairs: loan.acknowledgement_no
        ? [['Acknowledgement no.', loan.acknowledgement_no], ['Confirmed by', `OTP on ${loan.acknowledgement_mobile}`], ['Confirmed at', dateTimeText(loan.acknowledgement_verified_at)]]
        : [['Reference', loan.kfs_acknowledgement_reference || 'Not recorded']] },
      { heading: 'Repayments and receipts', columns: ['Receipt', 'Date', 'Type', 'Amount', 'Balance after', 'Mode / reference', 'Status'], money: [3, 4],
        rows: payments.map(p => [p.receipt_no, dateTimeText(p.timestamp), p.payment_type || 'Collection', rs(p.amount), rs(p.balance_after), [p.mode, p.payment_reference].filter(Boolean).join(' / '), p.status || 'Posted']),
        footer: payments.length ? ['', '', 'Total', rs(payments.filter(p => p.status !== 'Reversed').reduce((sum, p) => sum + Number(p.amount || 0), 0)), '', '', ''] : null,
        empty: 'No payments recorded yet.' },
      { heading: 'Instalment schedule', columns: ['No.', 'Due date', 'Instalment', 'Balance after'], money: [2, 3],
        rows: schedule.filter(row => Number(row.payment) > 0).map(row => [row.number, dayText(row.due_date), rs(row.payment), rs(row.closing)]),
        empty: 'This older loan has no stored schedule; instalments are counted from the loan date.' },
      { heading: 'Adjustments and servicing', columns: ['Date', 'Event', 'Amount', 'Details'], money: [2],
        rows: servicing.map(item => [dayText(item.timestamp || item.created_at), item.kind || item.event_type || item.type || item.strategy || 'Servicing', item.amount ? rs(item.amount) : '-', [item.reason || item.description, item.approval_reference ? `Approval ${item.approval_reference}` : ''].filter(Boolean).join(' - ')]),
        empty: 'No adjustments or servicing events.' },
    ],
  };
}

// ---------- Reports ----------
const COLUMN_PREFS = [
  ['receipt_no', 'Receipt'], ['timestamp', 'Date & time'], ['month', 'Month'], ['loan_id', 'Loan'], ['customer_id', 'Customer'],
  ['customer_name', 'Name'], ['name', 'Name'], ['area_name', 'Area'], ['loan_type', 'Plan'], ['borrow_date', 'Loan date'],
  ['principal', 'Loan amount'], ['installment', 'Instalment'], ['paid', 'Paid'], ['balance', 'Balance'], ['next_due_date', 'Next due'], ['status', 'Status'],
  ['remaining_installments', 'Left'], ['amount', 'Amount'], ['mode', 'Mode'], ['payment_type', 'Type'], ['collector_id', 'Collector'],
  ['customers', 'Customers'], ['active_loans', 'Active loans'], ['customers_with_dues', 'With dues'], ['today_collection', 'Today'],
  ['monthly_collection', 'This month'], ['outstanding', 'Outstanding'], ['total_disbursed', 'Disbursed'], ['count', 'Receipts'],
  ['collection', 'Collection'], ['total', 'Total'],
];
const SECTION_TITLES = { payments: 'Payments', loans: 'Loans', areas: 'Areas', collectors: 'Collectors', cashflow: 'Monthly collections' };

function tableFor(key, rows, nameLookup) {
  const objects = rows.filter(row => row && typeof row === 'object');
  const present = COLUMN_PREFS.filter(([k]) => objects.some(row => row[k] !== undefined && row[k] !== null && row[k] !== ''));
  const chosen = present.length ? present.slice(0, 10) : Object.keys(objects[0] || {}).filter(k => typeof objects[0][k] !== 'object').slice(0, 8).map(k => [k, pretty(k)]);
  const money = chosen.map(([k], i) => (MONEY_KEY.test(k) && !NOT_MONEY_KEY.test(k) ? i : -1)).filter(i => i >= 0);
  const cell = (k, row) => {
    if (k === 'loan_type') return planName(row[k]);
    if (k === 'collector_id') return nameLookup?.[row[k]] || row[k];
    if (k === 'payment_type' && !row[k]) return 'Collection';
    if (k === 'status' && !row[k] && row.receipt_no) return 'Posted';
    return formatValue(k, row[k]);
  };
  // Total every money column except per-instalment amounts.
  const summed = new Set(money.filter(i => chosen[i][0] !== 'installment'));
  const footer = summed.size && objects.length > 1 ? chosen.map(([k], i) => (summed.has(i) ? rs(objects.reduce((sum, row) => sum + Number(row[k] || 0), 0)) : i === 0 ? 'Total' : '')) : null;
  return { heading: SECTION_TITLES[key] || pretty(key), columns: chosen.map(([, label]) => label), rows: objects.map(row => chosen.map(([k]) => cell(k, row))), money, footer, empty: 'No records for this period.' };
}

export function reportDocument(report, { collectors = {} } = {}) {
  const skip = new Set(['title', 'generated_at']);
  const facts = [];
  const sections = [];
  for (const [key, value] of Object.entries(report || {})) {
    if (skip.has(key) || Array.isArray(value)) continue;
    if (key === 'customer' && value && typeof value === 'object') {
      sections.push({ heading: 'Customer', pairs: [
        ['Name', value.name], ['Customer ID', value.customer_id], ["Father's name", value.father_name], ['Mobile', `${value.mobile || '-'}${value.mobile_verified ? ' (verified)' : ''}`],
        ['Address', value.address], ['Area', value.area_name || value.area], ['Guarantor', value.guarantor || '-'], ['Status', value.status],
        ['Aadhaar', value.aadhaar_masked], ['Registered on', dayText(value.created_at)],
      ] });
      continue;
    }
    if (value && typeof value === 'object') {
      const pairs = Object.entries(value).filter(([k, v]) => typeof v !== 'object' && !k.startsWith('_') && k !== 'id').map(([k, v]) => [pretty(k), formatValue(k, v)]);
      if (pairs.length) sections.push({ heading: pretty(key), pairs });
      continue;
    }
    facts.push([pretty(key), formatValue(key, value)]);
  }
  if (facts.length) sections.unshift({ heading: 'Summary', pairs: facts });
  for (const [key, value] of Object.entries(report || {})) {
    if (Array.isArray(value)) sections.push(tableFor(key, value, collectors));
  }
  return { title: report?.title || 'Business report', sections };
}
