import { useEffect, useRef, useState } from "react";

type Props = {
  userUrl?: string;
  tourUrl?: string;
  userLabel: string;
  tourLabel: string;
  userPeakT?: number;
  tourPeakT?: number;
  phaseT?: number;
};

export function SideBySide({
  userUrl,
  tourUrl,
  userLabel,
  tourLabel,
  userPeakT = 0,
  tourPeakT = 0,
  phaseT,
}: Props) {
  const userRef = useRef<HTMLVideoElement>(null);
  const tourRef = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [sync, setSync] = useState(true);

  useEffect(() => {
    if (phaseT == null) return;
    const user = userRef.current;
    const tour = tourRef.current;
    const seek = (el: HTMLVideoElement | null, peak: number) => {
      if (!el || !el.duration) return;
      const t = Math.max(0, Math.min(el.duration * 0.98, phaseT * el.duration));
      if (Math.abs(el.currentTime - t) > 0.05) el.currentTime = t;
      void peak;
    };
    seek(user, userPeakT);
    seek(tour, tourPeakT);
  }, [phaseT, userPeakT, tourPeakT, userUrl, tourUrl]);

  useEffect(() => {
    const user = userRef.current;
    const tour = tourRef.current;
    if (!user || !tour || !sync) return;

    const onTime = () => {
      const mapped = user.currentTime - userPeakT + tourPeakT;
      if (!Number.isFinite(mapped)) return;
      const target = Math.max(0, Math.min(tour.duration || mapped, mapped));
      if (Math.abs(tour.currentTime - target) > 0.12) {
        tour.currentTime = target;
      }
    };
    user.addEventListener("timeupdate", onTime);
    return () => user.removeEventListener("timeupdate", onTime);
  }, [sync, userPeakT, tourPeakT, userUrl, tourUrl]);

  async function toggle() {
    const user = userRef.current;
    const tour = tourRef.current;
    if (!user) return;
    if (playing) {
      user.pause();
      tour?.pause();
      setPlaying(false);
      return;
    }
    try {
      if (tour && sync) {
        tour.currentTime = Math.max(0, user.currentTime - userPeakT + tourPeakT);
        await Promise.all([user.play(), tour.play()]);
      } else {
        await user.play();
        await tour?.play();
      }
      setPlaying(true);
    } catch {
      setPlaying(false);
    }
  }

  return (
    <div className="twin-compare">
      <div className="twin-compare__grid">
        <figure>
          <figcaption>You</figcaption>
          {userUrl ? (
            <video ref={userRef} src={userUrl} playsInline muted controls={false} />
          ) : (
            <div className="twin-compare__empty">Your swing</div>
          )}
          <p>{userLabel}</p>
        </figure>
        <figure>
          <figcaption>Tour player</figcaption>
          {tourUrl ? (
            <video ref={tourRef} src={tourUrl} playsInline muted controls={false} />
          ) : (
            <div className="twin-compare__empty">Their clip</div>
          )}
          <p>{tourLabel}</p>
        </figure>
      </div>
      <div className="twin-compare__bar">
        <button type="button" className="twin-btn" onClick={() => void toggle()} disabled={!userUrl}>
          {playing ? "Pause" : "Play both"}
        </button>
        <label>
          <input
            type="checkbox"
            checked={sync}
            onChange={(e) => setSync(e.target.checked)}
          />
          Sync to impact
        </label>
      </div>
    </div>
  );
}
