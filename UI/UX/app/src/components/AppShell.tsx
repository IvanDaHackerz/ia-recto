import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Menu, X } from "lucide-react";
const NAV_ITEMS = [
  { to: "/", label: "Ask", end: true },
  { to: "/history", label: "History" },
  { to: "/library", label: "Library" },
  { to: "/performance", label: "Performance" },
  { to: "/settings", label: "Settings" },
  { to: "/about", label: "Scope & limitations" },
];
export function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const mainRef = useRef<HTMLElement>(null);
  const previousPath = useRef(location.pathname);
  const menuRef = useRef<HTMLButtonElement>(null);
  const headerRef = useRef<HTMLElement>(null);
  const isChat = location.pathname === "/" || location.pathname.startsWith("/chat/") || location.pathname.startsWith("/saved/");
  useEffect(() => {
    const header = headerRef.current;
    if (!header) return;
    const measure = () => document.documentElement.style.setProperty("--masthead-height", `${header.getBoundingClientRect().height}px`);
    const observer = new ResizeObserver(measure);
    observer.observe(header);
    measure();
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    if (previousPath.current === location.pathname) return;
    previousPath.current = location.pathname;
    mainRef.current?.focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [location.pathname]);
  return (
    <div className={`site-shell${isChat ? " is-chat-route" : ""}`}>
      <a href="#main" className="skip-link">Skip to main content</a>
      <header ref={headerRef} className="site-header" onKeyDown={(event) => {
        if (event.key === "Escape" && menuOpen) { setMenuOpen(false); menuRef.current?.focus(); }
      }}>
        <div className="header-inner">
          <NavLink to="/" className="wordmark" onClick={() => setMenuOpen(false)}>Recto &amp; Co. Legal</NavLink>
          <button ref={menuRef} className="menu-toggle" type="button" aria-expanded={menuOpen} aria-controls="site-nav" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <X size={18} aria-hidden="true" /> : <Menu size={18} aria-hidden="true" />}
            {menuOpen ? "Close" : "Menu"}
          </button>
          <nav id="site-nav" aria-label="Primary" className={`site-nav${menuOpen ? " is-open" : ""}`}>
            {NAV_ITEMS.map(item => <NavLink key={item.to} to={item.to} end={item.end}
              onClick={() => setMenuOpen(false)} className={({ isActive }) => `nav-link${isActive ? " is-active" : ""}`}>{item.label}</NavLink>)}
          </nav>
        </div>
      </header>
      <div className="prototype-strip"><div className="page-width"><strong>Development preview.</strong> {location.pathname === "/performance" ? "Recorded development metrics · independent validation pending." : "Live classification, retrieval & AI explanations · source applicability remains under review."}</div></div>
      <main ref={mainRef} id="main" tabIndex={-1} className={`page-width main-content${isChat ? " workspace-main" : ""}`} key={location.pathname}><Outlet /></main>
      {!isChat && <footer className="site-footer page-width">
        <p>General information on selected Philippine labor and consumer concerns. This prototype does not provide professional legal advice.</p>
        <NavLink to="/about">Read the scope &amp; limitations</NavLink>
      </footer>}
    </div>
  );
}
