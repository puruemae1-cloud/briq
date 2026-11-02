"use client";

import { useCallback, useEffect, useState } from "react";
import {
  WelcomeDialog,
  welcomeHiddenForNow,
} from "@/components/WelcomePopup";
import {
  FlannelsPromoDialog,
  flannelsHiddenForNow,
} from "@/components/FlannelsPromoPopup";

type Step = "flannels" | "welcome" | null;

/**
 * Shows Flannels promo then the Briq welcome popup.
 * Closing one (X / backdrop / Esc) opens the next if it is still eligible.
 * `?welcome=preview` forces the full sequence.
 */
export function WelcomePopupGate() {
  const [step, setStep] = useState<Step>(null);
  const [force, setForce] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const preview = params.get("welcome") === "preview";
    setForce(preview);

    const showFlannels = preview || !flannelsHiddenForNow();
    const showWelcome = preview || !welcomeHiddenForNow();

    if (showFlannels) setStep("flannels");
    else if (showWelcome) setStep("welcome");
    else setStep(null);
  }, []);

  const afterFlannels = useCallback(() => {
    const showWelcome = force || !welcomeHiddenForNow();
    setStep(showWelcome ? "welcome" : null);
  }, [force]);

  const afterWelcome = useCallback(() => {
    setStep(null);
  }, []);

  if (step === "flannels") {
    return <FlannelsPromoDialog onClose={afterFlannels} />;
  }
  if (step === "welcome") {
    return <WelcomeDialog onClose={afterWelcome} />;
  }
  return null;
}
