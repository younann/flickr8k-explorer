import type { PropsWithChildren } from "react";
import { Link } from "react-router-dom";

export function AppShell({ children }: PropsWithChildren) {
  return <>
    <header className="masthead">
      <Link className="wordmark" to="/">FLICKR8K <span>LOCAL</span></Link>
      <nav aria-label="Primary"><Link to="/">Overview</Link><Link to="/gallery">Browse samples</Link><Link to="/radar">Research Radar</Link></nav>
    </header>
    {children}
  </>;
}
