import React, { useEffect, useState } from "react";
import { continueRender, delayRender } from "remotion";
import { loadFonts } from "./fonts";

/** Renders children only after every font face is resident, so text measurement is exact. */
export const FontGate: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [ready, setReady] = useState(false);
  const [handle] = useState(() => delayRender("fonts", { timeoutInMilliseconds: 60000 }));
  useEffect(() => {
    loadFonts().then(() => {
      setReady(true);
      continueRender(handle);
    });
  }, [handle]);
  return ready ? <>{children}</> : null;
};
