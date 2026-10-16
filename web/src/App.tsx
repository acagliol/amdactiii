import { useEffect } from "react";
import { Landing } from "./components/landing/Landing";
import { useHashRoute } from "./hooks/useHashRoute";
import { StationApp } from "./StationApp";

const PAGE_TITLES = {
  landing: "Multilönd · Catch mistakes before they're covered",
  station: "Multilönd · Worker Station",
};

/** "/" shows the product page for customers; "/#/station" is the working worker station. */
export function App() {
  const route = useHashRoute();

  useEffect(() => {
    document.title = PAGE_TITLES[route];
  }, [route]);

  return route === "station" ? <StationApp /> : <Landing />;
}
