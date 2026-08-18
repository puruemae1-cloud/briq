import { useCallback, useEffect, useRef, useState } from "react";
import type { Handedness, ProProfile, SwingSyncMarkers } from "@/lib/types";
import type { VideoDisplayStyle, SwingLandmarks } from "@/lib/swing-framing";
import { RORY_PORTRAIT_LANDMARKS } from "@/lib/swing-framing";
import {
  mapSyncedTourTime,
  swingPhaseNorm,
} from "@/lib/swing-sync";
import { ProSwingCanvas } from "./ProSwingCanvas";

type Props = {
  userUrl?: string;
  tourUrl?: string;
  userLabel: string;
  tourLabel: string;
  userSync?: SwingSyncMarkers;
  tourSync?: SwingSyncMarkers;
  phaseT?: number;
  pro?: ProProfile;
  handedness?: Handedness;
  tourIsReference?: boolean;
  tourVideoStyle?: VideoDisplayStyle;
  userVideoStyle?: VideoDisplayStyle;
  alignGuides?: SwingLandmarks;
  tourPoster?: string;
};

function AlignGuides({ marks }: { marks: SwingLandmarks }) {
  return (
    <div className="twin-align" aria-hidden>
      <span className="twin-align__h" style={{ top: `${marks.headY * 100}%` }} />
      <span className="twin-align__h" style={{ top: `${((marks.headY + marks.feetY) / 2) * 100}%` }} />
      <span className="twin-align__h" style={{ top: `${marks.ballY * 100}%` }} />
      <span className="twin-align__h" style={{ top: `${marks.feetY * 100}%` }} />
      <span className="twin-align__v" style={{ left: `${marks.backX * 100}%` }} />
      <span className="twin-align__v twin-align__v--ball" style={{ left: `${marks.ballX * 100}%` }} />
    </div>
  );
}

export function SideBySide({
  userUrl,
  tourUrl,
  userLabel,
  tourLabel,
  userSync,
  tourSync,
  phaseT,
  pro,
  handedness = "right",
  tourIsReference,
  tourVideoStyle,
  userVideoStyle,
  alignGuides = RORY_PORTRAIT_LANDMARKS,
  tourPoster,
}: Props) {
  const userRef = useRef<HTMLVideoElement>(null);
  const tourRef = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [sync, setSync] = useState(true);
  const [phaseNorm, setPhaseNorm] = useState(0);
  const rafRef = useRef(0);

  const hasSync = Boolean(userSync && tourSync);
  const useModel = !tourUrl && Boolean(pro && userSync && tourSync);

  const seekUser = useCallback(
    (t: number) => {
      const el = userRef.current;
      if (!el || !Number.isFinite(el.duration)) return;
      el.currentTime = Math.max(0, Math.min(el.duration * 0.99, t));
    },
    [],
  );

  const seekTour = useCallback(
    (userTime: number) => {
      if (!userSync || !tourSync) return;
      const mapped = mapSyncedTourTime(userTime, userSync, tourSync);
      const el = tourRef.current;
      if (el && Number.isFinite(el.duration)) {
        el.currentTime = Math.max(0, Math.min(el.duration * 0.99, mapped));
      }
      setPhaseNorm(swingPhaseNorm(userTime, userSync));
    },
    [userSync, tourSync],
  );

  useEffect(() => {
    if (phaseT == null || !userSync) return;
    const user = userRef.current;
    if (!user?.duration) return;
    const t = userSync.takeawayT + phaseT * (userSync.impactT - userSync.takeawayT);
    seekUser(t);
    seekTour(t);
  }, [phaseT, userSync, tourSync, userUrl, tourUrl, seekUser, seekTour]);

  useEffect(() => {
    const tour = tourRef.current;
    if (!tour || !tourUrl) return;
    const showFirst = () => {
      if (!Number.isFinite(tour.duration) || tour.duration <= 0) return;
      const t = tourSync?.takeawayT ?? Math.min(0.35, tour.duration * 0.08);
      try {
        tour.currentTime = t;
      } catch {
        /* ignore */
      }
    };
    tour.addEventListener("loadeddata", showFirst);
    tour.addEventListener("loadedmetadata", showFirst);
    if (tour.readyState >= 2) showFirst();
    return () => {
      tour.removeEventListener("loadeddata", showFirst);
      tour.removeEventListener("loadedmetadata", showFirst);
    };
  }, [tourUrl, tourSync]);

  useEffect(() => {
    if (!userUrl || !userSync) return;
    const user = userRef.current;
    if (!user) return;
    const onMeta = () => {
      seekUser(userSync.takeawayT);
      seekTour(userSync.takeawayT);
    };
    user.addEventListener("loadedmetadata", onMeta);
    if (user.readyState >= 1) onMeta();
    return () => user.removeEventListener("loadedmetadata", onMeta);
  }, [userUrl, userSync, tourSync, seekUser, seekTour]);

  useEffect(() => {
    const user = userRef.current;
    const tour = tourRef.current;
    if (!user || !sync || !hasSync) return;

    const onTime = () => {
      const t = user.currentTime;
      if (userSync && t >= userSync.endT && playing) {
        user.pause();
        tour?.pause();
        setPlaying(false);
        return;
      }
      if (tourUrl && tour) {
        const mapped = mapSyncedTourTime(t, userSync!, tourSync!);
        if (Math.abs(tour.currentTime - mapped) > 0.06) {
          tour.currentTime = mapped;
        }
      }
      setPhaseNorm(swingPhaseNorm(t, userSync!));
    };
    user.addEventListener("timeupdate", onTime);
    return () => user.removeEventListener("timeupdate", onTime);
  }, [sync, hasSync, userSync, tourSync, tourUrl, playing]);

  useEffect(() => {
    if (!playing || !userSync) return;
    const tick = () => {
      const user = userRef.current;
      if (user && !user.paused) {
        setPhaseNorm(swingPhaseNorm(user.currentTime, userSync));
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [playing, userSync]);

  async function toggle() {
    const user = userRef.current;
    const tour = tourRef.current;
    if (!user || !userSync) return;

    if (playing) {
      user.pause();
      tour?.pause();
      setPlaying(false);
      return;
    }

    try {
      seekUser(userSync.takeawayT);
      if (tourUrl && tour && tourSync) {
        tour.currentTime = mapSyncedTourTime(userSync.takeawayT, userSync, tourSync);
      }
      setPhaseNorm(0);
      await user.play();
      if (tourUrl && tour) await tour.play();
      setPlaying(true);
    } catch {
      setPlaying(false);
    }
  }

  function replaySegment() {
    if (!userSync) return;
    userRef.current?.pause();
    tourRef.current?.pause();
    setPlaying(false);
    seekUser(userSync.takeawayT);
    seekTour(userSync.takeawayT);
    setPhaseNorm(0);
  }

  return (
    <div className="twin-compare">
      <div className="twin-compare__grid">
        <figure>
          <figcaption>You · left</figcaption>
          {userUrl ? (
            <div className="twin-compare__video-wrap">
              <video
                ref={userRef}
                src={userUrl}
                playsInline
                muted
                controls={false}
                preload="auto"
                style={userVideoStyle}
              />
              <AlignGuides marks={alignGuides} />
            </div>
          ) : (
            <div className="twin-compare__empty">Your swing</div>
          )}
          <p>{userLabel}</p>
        </figure>
        <figure>
          <figcaption>
            {tourUrl ? `${pro?.name ?? "Tour"} · right` : pro?.name ?? "Tour player"}
          </figcaption>
          {tourUrl ? (
            <div className="twin-compare__video-wrap">
              <video
                ref={tourRef}
                src={tourUrl}
                poster={tourPoster}
                playsInline
                muted
                controls={false}
                preload="auto"
                style={tourVideoStyle}
              />
              <AlignGuides marks={alignGuides} />
            </div>
          ) : useModel && pro ? (
            <ProSwingCanvas
              pro={pro}
              handedness={handedness}
              phaseNorm={phaseNorm}
              label={`${pro.name} · learned model`}
            />
          ) : (
            <div className="twin-compare__empty">
              {tourPoster ? (
                <img src={tourPoster} alt="" className="twin-compare__poster" />
              ) : pro ? (
                `${pro.name} model`
              ) : (
                "Their clip"
              )}
            </div>
          )}
          <p>{tourLabel}</p>
        </figure>
      </div>
      <div className="twin-compare__bar">
        <button
          type="button"
          className="twin-btn"
          onClick={() => void toggle()}
          disabled={!userUrl || !hasSync}
        >
          {playing ? "Pause" : "Play synced swing"}
        </button>
        <button
          type="button"
          className="twin-btn twin-btn--ghost"
          onClick={replaySegment}
          disabled={!userUrl || !hasSync}
        >
          Replay takeaway → impact
        </button>
        <label>
          <input
            type="checkbox"
            checked={sync}
            onChange={(e) => setSync(e.target.checked)}
          />
          Sync arms up → impact
        </label>
      </div>
      {hasSync && userSync ? (
        <p className="twin-note twin-compare__sync">
          Synced: takeaway {userSync.takeawayT.toFixed(2)}s · top{" "}
          {userSync.topT.toFixed(2)}s · impact {userSync.impactT.toFixed(2)}s
          {tourIsReference
            ? " · Rory zoomed to match your body size"
            : tourUrl
              ? ""
              : " · upload Rory's clip on the right to replace the default"}
        </p>
      ) : null}
    </div>
  );
}
