import { useEffect, useState } from "react";

// Two pages without a router library: "/" is the product page, "/#/station" the worker station.
// Hash links work on any host, because the server only ever serves index.html.
export type Route = "landing" | "station";

export const STATION_HREF = "#/station";
export const LANDING_HREF = "#/";

function readRoute(): Route {
  return window.location.hash.startsWith("#/station") ? "station" : "landing";
}

export function useHashRoute(): Route {
  const [route, setRoute] = useState<Route>(readRoute);

  useEffect(() => {
    function onHashChange() {
      const next = readRoute();
      setRoute((previous) => {
        if (previous !== next) window.scrollTo(0, 0); // new page starts at the top
        return next;
      });
    }
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  return route;
}
