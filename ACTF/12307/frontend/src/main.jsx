import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Bell,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  ChevronRight,
  Clock3,
  FileText,
  IdCard,
  ListRestart,
  Loader2,
  MapPinned,
  RefreshCw,
  Repeat2,
  Search,
  Ticket,
  TrainFront,
  UserRoundCheck,
} from "lucide-react";
import "./styles.css";

const seatLabels = {
  business: "Business",
  first: "First class",
  second: "Second class",
};

const initialWorkspace = {
  trains: [],
  orders: [],
  notices: [],
  session: { session: false, trusted: false },
  enterprise: { invoices: [] },
};

const travelDates = [
  { id: "2026-04-24", label: "Thu, Apr 24" },
  { id: "2026-04-25", label: "Fri, Apr 25" },
  { id: "2026-04-26", label: "Sat, Apr 26" },
];

function money(value) {
  return `¥${Number(value || 0).toFixed(0)}`;
}

function classNames(...items) {
  return items.filter(Boolean).join(" ");
}

function seatStatus(train, seatClass) {
  const left = Number(train.seats?.[seatClass] || 0);
  const waiting = Number(train.waitlist?.[seatClass] || 0);
  if (left <= 0) return { left, waiting, text: "Sold out", tone: "sold" };
  if (left < 6) return { left, waiting, text: `${left} left`, tone: "low" };
  return { left, waiting, text: `${left} available`, tone: "ok" };
}

function unique(items) {
  return [...new Set(items.filter(Boolean))];
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw: text };
  }
  if (!res.ok) {
    const error = new Error(data.error || `HTTP ${res.status}`);
    error.status = res.status;
    error.data = data;
    throw error;
  }
  return data;
}

function Toast({ message }) {
  return <div className={classNames("toast", message && "is-visible")}>{message}</div>;
}

function TopBar({ activeTab, setActiveTab, loading, refresh, origin, destination }) {
  const tabs = [
    ["trips", TrainFront, "Trips"],
    ["desk", Building2, "Desk"],
    ["corporate", BriefcaseBusiness, "Corp"],
  ];
  return (
    <header className="topbar">
      <div className="topbar-main">
        <div>
          <span className="route-kicker">12307</span>
          <h1>{origin || "Origin"} <span>→</span> {destination || "Destination"}</h1>
        </div>
        <button className="icon-button light" onClick={refresh} aria-label="Refresh workspace" title="Refresh workspace">
          {loading ? <Loader2 className="spin" size={20} /> : <RefreshCw size={20} />}
        </button>
      </div>
      <nav className="tabbar" aria-label="Workspace">
        {tabs.map(([id, Icon, label]) => (
          <button key={id} className={classNames(activeTab === id && "is-active")} onClick={() => setActiveTab(id)}>
            <Icon size={17} />
            <span>{label}</span>
          </button>
        ))}
      </nav>
    </header>
  );
}

function RouteSearch({
  seatClass,
  setSeatClass,
  requestIdentity,
  session,
  origin,
  setOrigin,
  destination,
  setDestination,
  journeyDate,
  setJourneyDate,
  originOptions,
  destinationOptions,
  swapRoute,
  searchTrip,
  resultCount,
  passengerName,
  setPassengerName,
}) {
  return (
    <section className="search-card">
      <div className="hero-photo" aria-hidden="true" />
      <div className="search-body">
        <div className="route-grid">
          <div>
            <span className="field-label">From</span>
            <select
              id="origin-station"
              name="originStation"
              value={origin}
              onChange={event => setOrigin(event.target.value)}
              aria-label="From station"
            >
              {originOptions.map(station => <option key={station} value={station}>{station}</option>)}
            </select>
          </div>
          <button className="swap-button" onClick={swapRoute} aria-label="Swap route" title="Swap route">
            <Repeat2 size={20} />
          </button>
          <div className="align-right">
            <span className="field-label">To</span>
            <select
              id="destination-station"
              name="destinationStation"
              value={destination}
              onChange={event => setDestination(event.target.value)}
              aria-label="To station"
            >
              {destinationOptions.map(station => <option key={station} value={station}>{station}</option>)}
            </select>
          </div>
        </div>

        <div className="date-row">
          {travelDates.map(item => (
            <button
              key={item.id}
              className={classNames("date-chip", journeyDate === item.id && "is-active")}
              onClick={() => setJourneyDate(item.id)}
            >
              <CalendarDays size={16} />
              {item.label}
            </button>
          ))}
        </div>

        <div className="seat-tabs">
          {Object.keys(seatLabels).map(seat => (
            <button
              key={seat}
              className={seatClass === seat ? "is-active" : ""}
              onClick={() => setSeatClass(seat)}
            >
              {seatLabels[seat]}
            </button>
          ))}
        </div>

        <div className="identity-strip">
          <div>
            <span className="field-label">Real-name ticketing</span>
            <strong>{session?.trusted ? `${session.passenger || "Passenger"} verified` : "Mobile passenger pending"}</strong>
            <input
              className="passenger-input"
              name="passengerName"
              value={passengerName}
              onChange={event => setPassengerName(event.target.value)}
              aria-label="Passenger name"
            />
          </div>
          <button className="primary-mini" onClick={requestIdentity}>
            <IdCard size={16} />
            Continue
          </button>
        </div>

        <div className="search-action-row">
          <button className="primary search-submit" onClick={searchTrip}>
            <Search size={17} />
            Search trains
          </button>
          <span>{resultCount} found</span>
        </div>
      </div>
    </section>
  );
}

function StatsStrip({ trains, seatClass }) {
  const capacity = trains.reduce((sum, train) => sum + Number(train.seats?.[seatClass] || 0), 0);
  const waiting = trains.reduce((sum, train) => sum + Number(train.waitlist?.[seatClass] || 0), 0);
  return (
    <section className="stats-strip">
      <div><TrainFront size={18} /><span>Trains</span><strong>{trains.length}</strong></div>
      <div><Ticket size={18} /><span>Seats</span><strong>{capacity}</strong></div>
      <div><ListRestart size={18} /><span>Waitlist</span><strong>{waiting}</strong></div>
    </section>
  );
}

function TrainCard({ train, seatClass, reserve, requestBoard }) {
  const status = seatStatus(train, seatClass);
  const fare = Number(train.price || 0) * (seatClass === "business" ? 2.7 : seatClass === "first" ? 1.45 : 1);
  return (
    <article className="train-card">
      <div className="train-row">
        <div className="station-block">
          <time>{train.depart}</time>
          <strong>{train.origin}</strong>
          <small>{train.stationCode}</small>
        </div>
        <div className="train-line">
          <strong>{train.id}</strong>
          <span />
          <small><Clock3 size={13} /> {train.duration}</small>
        </div>
        <div className="station-block align-right">
          <time>{train.arrive}</time>
          <strong>{train.destination}</strong>
          <small>{train.gate}</small>
        </div>
      </div>
      <div className="train-bottom">
        <div>
          <span className={classNames("seat-state", status.tone)}>{status.text}</span>
          <small>{seatLabels[seatClass]} · {status.waiting} waiting</small>
        </div>
        <div className="fare-action">
          <span>From <strong>{money(fare)}</strong></span>
          <button onClick={() => reserve(train, status)}>{status.left > 0 ? "Reserve" : "Join waitlist"}</button>
        </div>
      </div>
      <button className="text-link train-detail-link" onClick={() => requestBoard(train.stationCode)}>
        <MapPinned size={15} />
        Boarding info
      </button>
    </article>
  );
}

function TripsView({
  workspace,
  trains,
  seatClass,
  setSeatClass,
  reserve,
  requestIdentity,
  requestBoard,
  origin,
  setOrigin,
  destination,
  setDestination,
  journeyDate,
  setJourneyDate,
  originOptions,
  destinationOptions,
  swapRoute,
  searchTrip,
  passengerName,
  setPassengerName,
}) {
  return (
    <>
      <RouteSearch
        seatClass={seatClass}
        setSeatClass={setSeatClass}
        requestIdentity={requestIdentity}
        session={workspace.session}
        origin={origin}
        setOrigin={setOrigin}
        destination={destination}
        setDestination={setDestination}
        journeyDate={journeyDate}
        setJourneyDate={setJourneyDate}
        originOptions={originOptions}
        destinationOptions={destinationOptions}
        swapRoute={swapRoute}
        searchTrip={searchTrip}
        resultCount={trains.length}
        passengerName={passengerName}
        setPassengerName={setPassengerName}
      />
      <StatsStrip trains={trains} seatClass={seatClass} />
      <section className="panel unframed">
        <div className="section-title">
          <h2>Trains</h2>
          <span className="section-meta">{seatLabels[seatClass]}</span>
        </div>
        <div className="train-list">
          {trains.length ? trains.map(train => (
            <TrainCard key={train.id} train={train} seatClass={seatClass} reserve={reserve} requestBoard={requestBoard} />
          )) : <p className="empty panel-empty">No trains match this route.</p>}
        </div>
      </section>
      <section className="panel">
        <div className="section-title">
          <h2>Recent orders</h2>
          <span>{workspace.orders.length}</span>
        </div>
        <div className="order-list">
          {workspace.orders.length ? workspace.orders.slice(0, 5).map(order => (
            <div className="order-row" key={order.id}>
              <div>
                <strong>{order.trainId} · {order.origin} to {order.destination}</strong>
                <small>{seatLabels[order.seatClass]} · {order.passenger}</small>
              </div>
              <span className={classNames("pill", order.status)}>{order.status}</span>
            </div>
          )) : <p className="empty">Your booked trips will appear here.</p>}
        </div>
      </section>
    </>
  );
}

function DeskView({ notices, deskQuery, setDeskQuery, ticketResults, searchTickets, deskMemo, setDeskMemo, postDeskAdjustment, postNotice }) {
  return (
    <>
      <section className="panel desk-hero">
        <div>
          <span className="field-label">Station service desk</span>
          <h2>Maintenance queue</h2>
          <p>Ticket lookup, adjustment notes, partner notice publishing, and reconciliation metadata share one desk workflow.</p>
        </div>
        <MapPinned size={44} />
      </section>
      <section className="panel">
        <div className="section-title">
          <h2>Ticket adjustment</h2>
          <button className="icon-button" onClick={searchTickets} aria-label="Search tickets" title="Search tickets"><Search size={18} /></button>
        </div>
        <div className="form-grid">
          <label>
            <span>Ticket or passenger</span>
            <input value={deskQuery} onChange={event => setDeskQuery(event.target.value)} placeholder="T-HGH-7608-019" />
          </label>
          <label>
            <span>Adjustment memo</span>
            <textarea value={deskMemo} onChange={event => setDeskMemo(event.target.value)} placeholder="Service desk memo" />
          </label>
          <div className="button-row">
            <button className="primary" onClick={postDeskAdjustment}>Record adjustment</button>
          </div>
        </div>
        <div className="ticket-list">
          {ticketResults.map(ticket => (
            <div className="ticket-row" key={ticket.ticketNo}>
              <strong>{ticket.ticketNo}</strong>
              <span>{ticket.passenger} · {ticket.trainId} · {ticket.status}</span>
            </div>
          ))}
        </div>
      </section>
      <section className="panel">
        <div className="section-title">
          <h2>Station notices</h2>
          <button className="text-link" onClick={postNotice}><Bell size={16} /> Publish sample</button>
        </div>
        <div className="notice-list">
          {notices.length ? notices.slice(0, 6).map(notice => (
            <div className="notice-row" key={notice.slug}>
              <strong>{notice.title}</strong>
              <small>{notice.body}</small>
            </div>
          )) : <p className="empty">No current station notices.</p>}
        </div>
      </section>
    </>
  );
}

function CorporateView({ invoices, batchId, setBatchId, report, pollReport, prepareReceipt, scheduleBatch }) {
  return (
    <>
      <section className="panel corporate-hero">
        <div>
          <span className="field-label">Corporate settlement</span>
          <h2>Receipt workspace</h2>
          <p>Enterprise invoices, carrier receipt preparation, scheduling, and reconciliation output are handled here.</p>
        </div>
        <FileText size={44} />
      </section>
      <section className="panel">
        <div className="section-title">
          <h2>Enterprise invoices</h2>
          <span>{invoices.length}</span>
        </div>
        <div className="invoice-list">
          {invoices.map(invoice => (
            <div className="invoice-row" key={invoice.invoiceId}>
              <div>
                <strong>{invoice.invoiceId}</strong>
                <small>{invoice.accountId} · {invoice.stationCode}</small>
              </div>
              <span className="pill open">{invoice.disputeState}</span>
            </div>
          ))}
        </div>
      </section>
      <section className="panel">
        <div className="section-title">
          <h2>Reconciliation receipt</h2>
          <button className="icon-button" onClick={pollReport} aria-label="Poll report" title="Poll report"><RefreshCw size={18} /></button>
        </div>
        <div className="form-grid">
          <label>
            <span>Batch ID</span>
            <input value={batchId} onChange={event => setBatchId(event.target.value)} placeholder="B..." />
          </label>
          <div className="button-row">
            <button className="secondary" onClick={prepareReceipt}>Prepare</button>
            <button className="primary" onClick={scheduleBatch}>Schedule</button>
          </div>
        </div>
        <pre className="report-preview">{report ? JSON.stringify(report, null, 2) : "No report selected."}</pre>
      </section>
    </>
  );
}

function App() {
  const [workspace, setWorkspace] = useState(initialWorkspace);
  const [activeTab, setActiveTab] = useState("trips");
  const [seatClass, setSeatClass] = useState("second");
  const [origin, setOrigin] = useState("Beijing South");
  const [destination, setDestination] = useState("Shanghai Hongqiao");
  const [journeyDate, setJourneyDate] = useState("2026-04-25");
  const [passengerName, setPassengerName] = useState("Mobile Passenger");
  const [toast, setToast] = useState("");
  const [loading, setLoading] = useState(false);
  const [deskQuery, setDeskQuery] = useState("T-HGH-7608-019");
  const [deskMemo, setDeskMemo] = useState("Customer desk reprice review");
  const [ticketResults, setTicketResults] = useState([]);
  const [batchId, setBatchId] = useState("");
  const [report, setReport] = useState(null);

  const invoices = useMemo(() => workspace.enterprise?.invoices || [], [workspace.enterprise]);
  const originOptions = useMemo(() => {
    const options = unique(workspace.trains.map(train => train.origin));
    return options.includes(origin) ? options : [origin, ...options];
  }, [workspace.trains, origin]);
  const destinationOptions = useMemo(() => {
    const options = unique(workspace.trains.map(train => train.destination));
    return options.includes(destination) ? options : [destination, ...options];
  }, [workspace.trains, destination]);
  const visibleTrains = useMemo(() => {
    return workspace.trains.filter(train => train.origin === origin && train.destination === destination);
  }, [workspace.trains, origin, destination]);

  function flash(message) {
    setToast(message);
    window.clearTimeout(flash.timer);
    flash.timer = window.setTimeout(() => setToast(""), 2600);
  }

  async function loadWorkspace() {
    setLoading(true);
    try {
      const data = await api("/api/mobile/workspace");
      setWorkspace({ ...initialWorkspace, ...data });
    } finally {
      setLoading(false);
    }
  }

  async function requestIdentity() {
    try {
      await api("/api/mobile/identity/continue", {
        method: "POST",
        body: JSON.stringify({
          passenger: passengerName || "Passenger",
          relayState: { next: "rail://continue/seat-hold", flow: ["seat-hold"] },
          partnerMetadata: {
            entityID: "railway-partner",
            compatBinding: "x-accel",
            role: "PassengerIdentityProvider",
          },
          assertion: "<Assertion><Audience>12307</Audience><NameID>mobile-passenger</NameID><Signature>RelayState</Signature></Assertion>",
          trustLevel: ["mobile", "partner"],
          stationCode: "HGH",
        }),
      });
      flash("Identity continuation accepted");
      await loadWorkspace();
    } catch (error) {
      flash(error.data?.error || "Identity pending");
    }
  }

  function swapRoute() {
    setOrigin(destination);
    setDestination(origin);
  }

  function searchTrip() {
    flash(`${visibleTrains.length} trains found`);
  }

  async function reserve(train, status) {
    try {
      if (status.left <= 0) {
        await api("/api/mobile/orders/hold", {
          method: "POST",
          body: JSON.stringify({ trainId: train.id, seatClass, holdMode: "waitlist" }),
        });
      }
      const passenger = passengerName || workspace.session?.passenger || "Passenger";
      const data = await api("/api/mobile/orders", {
        method: "POST",
        body: JSON.stringify({ trainId: train.id, seatClass, passenger }),
      });
      flash(data.order.status === "waitlisted" ? `${data.order.trainId} waitlisted` : `${data.order.trainId} reserved`);
      await loadWorkspace();
    } catch (error) {
      flash(error.data?.error === "identity_continuation_required" ? "Complete passenger identity first" : error.data?.error || "Reservation failed");
    }
  }

  async function requestBoard(stationCode = "HGH") {
    const data = await api(`/api/mobile/coach/board?stationCode=${encodeURIComponent(stationCode)}`, { headers: {} });
    flash(`Coach board ${data.stream || "standard"}`);
  }

  async function searchTickets() {
    const data = await api(`/api/desk/tickets/search?q=${encodeURIComponent(deskQuery)}`);
    setTicketResults(data.tickets || []);
    flash("Ticket index refreshed");
  }

  async function postDeskAdjustment() {
    await api("/api/desk/tickets/adjust", {
      method: "POST",
      body: JSON.stringify({ ticketNo: deskQuery || "T-HGH-7608-019", memo: deskMemo, delta: 0 }),
    });
    flash("Adjustment recorded");
  }

  async function postNotice() {
    await api("/api/desk/notices", {
      method: "POST",
      body: JSON.stringify({
        stationCode: "HGH",
        title: "Partner feed maintenance",
        body: "Temporary notice for carrier desk handoff.",
        proxyHint: "feed=partner",
      }),
    });
    flash("Notice published");
    await loadWorkspace();
  }

  async function pollReport() {
    if (!batchId) {
      flash("Enter a batch ID");
      return;
    }
    const data = await api(`/api/corporate/reconciliation/${encodeURIComponent(batchId)}`);
    setReport(data.report || data);
    flash("Reconciliation refreshed");
  }

  async function prepareReceipt() {
    flash("Open an order batch before preparing");
  }

  async function scheduleBatch() {
    if (!batchId) {
      flash("Enter a batch ID");
      return;
    }
    const data = await api("/api/corporate/settlement/schedule", {
      method: "POST",
      body: JSON.stringify({ batchId }),
    });
    setReport(data);
    flash(data.scheduled ? "Batch scheduled" : "Batch held for review");
  }

  useEffect(() => {
    loadWorkspace().catch(() => flash("Services are starting"));
  }, []);

  return (
    <>
      <main className="app-shell">
        <TopBar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          loading={loading}
          refresh={() => loadWorkspace().then(() => flash("Workspace refreshed"))}
          origin={origin}
          destination={destination}
        />
        {activeTab === "trips" && (
          <TripsView
            workspace={workspace}
            trains={visibleTrains}
            seatClass={seatClass}
            setSeatClass={setSeatClass}
            reserve={reserve}
            requestIdentity={requestIdentity}
            requestBoard={requestBoard}
            origin={origin}
            setOrigin={setOrigin}
            destination={destination}
            setDestination={setDestination}
            journeyDate={journeyDate}
            setJourneyDate={setJourneyDate}
            originOptions={originOptions}
            destinationOptions={destinationOptions}
            swapRoute={swapRoute}
            searchTrip={searchTrip}
            passengerName={passengerName}
            setPassengerName={setPassengerName}
          />
        )}
        {activeTab === "desk" && (
          <DeskView
            notices={workspace.notices}
            deskQuery={deskQuery}
            setDeskQuery={setDeskQuery}
            ticketResults={ticketResults}
            searchTickets={searchTickets}
            deskMemo={deskMemo}
            setDeskMemo={setDeskMemo}
            postDeskAdjustment={postDeskAdjustment}
            postNotice={postNotice}
          />
        )}
        {activeTab === "corporate" && (
          <CorporateView
            invoices={invoices}
            batchId={batchId}
            setBatchId={setBatchId}
            report={report}
            pollReport={pollReport}
            prepareReceipt={prepareReceipt}
            scheduleBatch={scheduleBatch}
          />
        )}
      </main>
      <Toast message={toast} />
    </>
  );
}

createRoot(document.getElementById("root")).render(<App />);
