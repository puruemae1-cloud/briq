import { useCallback, useEffect, useRef, useState } from "react";
import type { Handedness, ProProfile, SwingSyncMarkers } from "@/lib/types";
import type { VideoDisplayStyle, SwingLandmarks } from "@/lib/swing-framing";
import { RORY_PORTRAIT_LANDMARKS } from "@/lib/swing-framing";
import {
  mapSyncedTourTime,
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
  const [sync, setSync] = useState(false);
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

  const seekTour = useCallback(
    (userTime: number, warp: boolean) => {
      const el = tourRef.current;
      if (!el || !Number.isFinite(el.duration) || !tourSync) return;
      const mapped = warp && userSync
        ? mapSyncedTourTime(userTime, userSync, tourSync)
        : swingAddressT(tourSync) + Math.max(0, userTime - (userSync ? swingAddressT(userSync) : 0));
      const start = tourIsReference ? 0 : swingAddressT(tourSync);
      const target = warp ? mapped : Math.max(start, mapped);
      el.currentTime = Math.max(0, Math.min(el.duration * 0.99, target));
      if (userSync) setPhaseNorm(swingPhaseNorm(userTime, userSync));
    },
    [userSync, tourSync, tourIsReference],
  );

  useEffect(() => {
    if (phaseT == null || !userSync) return;
    const user = userRef.current;
    if (!user?.duration) return;
    const t = userSync.takeawayT + phaseT * (userSync.impactT - userSync.takeawayT);
    seekUser(t);
    seekTour(t, sync);
  }, [phaseT, userSync, tourSync, userUrl, tourUrl, seekUser, seekTour, sync]);

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

    const maybeStop = () => {
      if (user.currentTime >= userEnd) {
        user.pause();
        userDoneRef.current = true;
      }
      if (tour && tour.currentTime >= tourEnd) {
        tour.pause();
        tourDoneRef.current = true;
      }
      if (userDoneRef.current && (tourDoneRef.current || !tour)) {
        setPlaying(false);
      }
      setPhaseNorm(swingPhaseNorm(user.currentTime, userSync));
    };

    const onUser = () => {
      if (sync && tour && userSync && tourSync) {
        const mapped = mapSyncedTourTime(user.currentTime, userSync, tourSync);
        if (Math.abs(tour.currentTime - mapped) > 0.06) {
          tour.currentTime = mapped;
        }
      }
      maybeStop();
    };
    const onTour = () => maybeStop();
    const onUserEnded = () => {
      userDoneRef.current = true;
      maybeStop();
    };
    const onTourEnded = () => {
      tourDoneRef.current = true;
      maybeStop();
    };

    user.addEventListener("timeupdate", onUser);
    user.addEventListener("ended", onUserEnded);
    tour?.addEventListener("timeupdate", onTour);
    tour?.addEventListener("ended", onTourEnded);
    return () => {
      user.removeEventListener("timeupdate", onUser);
      user.removeEventListener("ended", onUserEnded);
      tour?.removeEventListener("timeupdate", onTour);
      tour?.removeEventListener("ended", onTourEnded);
    };
  }, [playing, sync, userSync, tourSync, tourIsReference]);

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
      const userStart = swingAddressT(userSync);
      const tourStart = tourIsReference
        ? 0
        : tourSync
          ? swingAddressT(tourSync)
          : 0;
      seekUser(userStart);
      if (tourUrl && tour) {
        tour.currentTime = Math.max(
          0,
          Math.min(tour.duration * 0.99, tourStart),
        );
        tour.playbackRate = 1;
      }
      user.playbackRate = 1;
      userDoneRef.current = false;
      tourDoneRef.current = false;
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
    const userStart = swingAddressT(userSync);
    seekUser(userStart);
    const tour = tourRef.current;
    if (tour && tourSync) {
      tour.currentTime = tourIsReference ? 0 : swingAddressT(tourSync);
    }
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
          <input
            type="checkbox"
            checked={sync}
            onChange={(e) => setSync(e.target.checked)}
          />
          Warp speed to hit impact together
        </label>
      </div>
      {hasSync && userSync ? (
        <p className="twin-note twin-compare__sync">
          Synced: takeaway {userSync.takeawayT.toFixed(2)}s · top{" "}
          {userSync.topT.toFixed(2)}s · impact {userSync.impactT.toFixed(2)}s
          {tourIsReference
            ? " · same 1x speed · address → finish · your body zoomed to Rory"
            : tourUrl
              ? ""
              : " · upload Rory's clip on the right to replace the default"}
        </p>
      ) : null}
    </div>
  );
}
