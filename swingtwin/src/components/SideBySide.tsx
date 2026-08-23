import { useCallback, useEffect, useRef, useState } from "react";
import type { Handedness, ProProfile, SwingSyncMarkers } from "@/lib/types";
import type { VideoDisplayStyle, SwingLandmarks } from "@/lib/swing-framing";
import { RORY_PORTRAIT_LANDMARKS } from "@/lib/swing-framing";
import {
  swingPhaseNorm,
  swingAddressT,
  swingFinishT,
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
  const [sync] = useState(true);
  const [phaseNorm, setPhaseNorm] = useState(0);
  const rafRef = useRef(0);
  const userDoneRef = useRef(false);
  const tourDoneRef = useRef(false);

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


  useEffect(() => {
    if (phaseT == null || !userSync) return;
    const user = userRef.current;
    if (!user?.duration) return;
    const t = userSync.takeawayT + phaseT * (userSync.impactT - userSync.takeawayT);
    seekUser(t);
  }, [phaseT, userSync, userUrl, seekUser]);

  useEffect(() => {
    const tour = tourRef.current;
    if (!tour || !tourUrl) return;
    const showFirst = () => {
      if (!Number.isFinite(tour.duration) || tour.duration <= 0) return;
      const t = tourIsReference ? 0 : tourSync ? swingAddressT(tourSync) : 0;
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
  }, [tourUrl, tourSync, tourIsReference]);

  useEffect(() => {
    if (!userUrl || !userSync) return;
    const user = userRef.current;
    if (!user) return;
    const onMeta = () => {
      const t = swingAddressT(userSync);
      seekUser(t);
      const tour = tourRef.current;
      if (tour && tourSync) {
        const start = tourIsReference ? 0 : swingAddressT(tourSync);
        tour.currentTime = Math.max(0, Math.min(tour.duration * 0.99, start));
      }
    };
    user.addEventListener("loadedmetadata", onMeta);
    if (user.readyState >= 1) onMeta();
    return () => user.removeEventListener("loadedmetadata", onMeta);
  }, [userUrl, userSync, tourSync, tourIsReference, seekUser]);

  useEffect(() => {
    const user = userRef.current;
    const tour = tourRef.current;
    if (!playing || !user || !userSync) return;

    const userEnd = swingFinishT(userSync, user.duration);
    const tourEnd = tour
      ? tourIsReference && Number.isFinite(tour.duration)
        ? tour.duration * 0.995
        : tourSync
          ? swingFinishT(tourSync, tour.duration)
          : tour.duration * 0.995
      : Infinity;

    let raf = 0;
    const tick = () => {
      const t = user.currentTime;
      setPhaseNorm(swingPhaseNorm(t, userSync));

      // Stop user at finish
      if (t >= userEnd && !userDoneRef.current) {
        user.pause();
        userDoneRef.current = true;
      }
      // Stop tour at finish
      if (tour && tour.currentTime >= tourEnd && !tourDoneRef.current) {
        tour.pause();
        tourDoneRef.current = true;
      }
      if (userDoneRef.current && (tourDoneRef.current || !tour)) {
        setPlaying(false);
        return;
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, userSync, tourSync, tourIsReference]);

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
      const userStart = swingAddressT(userSync);
      const tourStart = tourIsReference
        ? 0
        : tourSync
          ? swingAddressT(tourSync)
          : 0;

      const userEnd = swingFinishT(userSync, user.duration);
      const userLen = Math.max(0.5, userEnd - userStart);

      const tourEl = tourUrl && tour ? tour : null;
      const tourLen = tourEl && tourSync
        ? Math.max(0.5, swingFinishT(tourSync, tourEl.duration) - tourStart)
        : tourEl && tourIsReference && Number.isFinite(tourEl.duration)
          ? Math.max(0.5, tourEl.duration * 0.995 - tourStart)
          : null;

      // Always match Rory timing: keep Rory at 1x, slow/speed up the user so
      // both address → finish end at the same wall-clock time.
      // If user's timeline segment is shorter, userRate < 1 (slow down).
      let userRate = 1;
      if (tourLen != null && tourLen > 0) {
        userRate = Math.max(0.1, Math.min(4, userLen / tourLen));
      }

      seekUser(userStart);
      if (tourEl) {
        tourEl.currentTime = Math.max(0, Math.min(tourEl.duration * 0.995, tourStart));
        tourEl.playbackRate = 1;
      }
      user.playbackRate = userRate;
      userDoneRef.current = false;
      tourDoneRef.current = false;
      setPhaseNorm(0);
      await user.play();
      if (tourEl) await tourEl.play();
      setPlaying(true);
    } catch {
      setPlaying(false);
    }
  }

  function replaySegment() {
    void toggle();
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
          {playing ? "Pause" : "Play swing"}
        </button>
        <button
          type="button"
          className="twin-btn twin-btn--ghost"
          onClick={replaySegment}
          disabled={!userUrl || !hasSync}
        >
          Replay address → finish
        </button>
        <label>
          <input type="checkbox" checked={true} disabled />
          같은 속도로 처음부터 끝까지
        </label>
      </div>
      {hasSync && userSync ? (
        <p className="twin-note twin-compare__sync">
          Synced: takeaway {userSync.takeawayT.toFixed(2)}s · top{" "}
          {userSync.topT.toFixed(2)}s · impact {userSync.impactT.toFixed(2)}s
          {tourIsReference
            ? " · 쌍둥이 속도 · address → finish · your body zoomed to Rory"
            : tourUrl
              ? ""
              : " · upload Rory's clip on the right to replace the default"}
        </p>
      ) : null}
    </div>
  );
}
