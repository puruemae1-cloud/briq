import { useCallback, useEffect, useRef, useState } from "react";
import { analyzePair } from "@/lib/analyze";
import { applyHandedness, captureView, fuseSkeletons, sampleCompareSet } from "@/lib/capture";
import { TOUR_STYLE } from "@/lib/anatomy";
import { defaultProId, getPro } from "@/lib/pros";
import { getReferenceClip } from "@/lib/reference-clips";
import { useTwinStore } from "@/lib/store";
import { saveClip, clipObjectUrl, loadClip, deleteClip } from "@/lib/video-store";
import { autoFrameSwingVideo, detectBodyCropFromUrl, cropToVideoStyle, tourMatchScale } from "@/lib/swing-framing";
import type { BodyFrameMeta, VideoDisplayStyle } from "@/lib/swing-framing";
import { detectSwingSync, modelSyncFromUser, syncFromSkeleton } from "@/lib/swing-sync";
import type { SkeletonFrame, SwingSyncMarkers, ViewCapture } from "@/lib/types";
import { SideBySide } from "./SideBySide";
import { Swing3D } from "./Swing3D";
import { PlayerPicker } from "./PlayerPicker";
import { PhaseOverlay } from "./PhaseOverlay";
import { UploadProgressBar } from "./UploadProgressBar";

type UploadSlot = "face" | "dtl";
type UploadProgressState = {
  slot: UploadSlot;
  label: string;
  percent: number;
};

async function loadVideo(src: string) {
  const video = document.createElement("video");
  video.src = src;
  video.muted = true;
  video.playsInline = true;
  video.crossOrigin = "anonymous";
  await new Promise<void>((resolve, reject) => {
    video.onloadedmetadata = () => resolve();
    video.onerror = () => reject(new Error("Could not read that video."));
  });
  return video;
}

async function fileToVideo(file: File) {
  const url = URL.createObjectURL(file);
  const video = await loadVideo(url);
  return { video, url };
}

function isBlobUrl(url?: string) {
  return Boolean(url?.startsWith("blob:"));
}

export function CompareStudio() {
  const [myFace, setMyFace] = useState<File | null>(null);
  const [myDtl, setMyDtl] = useState<File | null>(null);
  const [userUrl, setUserUrl] = useState<string | undefined>();
  const [tourUrl, setTourUrl] = useState<string | undefined>();
  const [busy, setBusy] = useState<string | null>(null);
  const [syncBusy, setSyncBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [phaseT, setPhaseT] = useState<number | undefined>();
  const [tourFrames, setTourFrames] = useState<SkeletonFrame[] | undefined>();
  const [userFileName, setUserFileName] = useState<string>();
  const [tourFileName, setTourFileName] = useState<string>();
  const [liveUserSync, setLiveUserSync] = useState<SwingSyncMarkers | undefined>();
  const [liveTourSync, setLiveTourSync] = useState<SwingSyncMarkers | undefined>();
  const [refTourCapture, setRefTourCapture] = useState<ViewCapture | undefined>();
  const [usingReference, setUsingReference] = useState(false);
  const [userFrameMeta, setUserFrameMeta] = useState<BodyFrameMeta | undefined>();
  const [tourDisplayStyle, setTourDisplayStyle] = useState<VideoDisplayStyle | undefined>();
  const [userDisplayStyle, setUserDisplayStyle] = useState<VideoDisplayStyle | undefined>();
  const [uploadProgress, setUploadProgress] = useState<UploadProgressState | null>(
    null,
  );

  const userFaceInputRef = useRef<HTMLInputElement>(null);
  const userDtlInputRef = useRef<HTMLInputElement>(null);
  const tourRevokeRef = useRef<(() => void) | null>(null);
  const tourLoadGen = useRef(0);

  const preferredProId = useTwinStore((s) => s.preferredProId);
  const handedness = useTwinStore((s) => s.handedness);
  const result = useTwinStore((s) => s.lastResult);
  const thumbs = useTwinStore((s) => s.lastThumbs);
  const skeleton = useTwinStore((s) => s.lastSkeleton) ?? [];
  const setPreferredPro = useTwinStore((s) => s.setPreferredPro);
  const setHandedness = useTwinStore((s) => s.setHandedness);
  const saveAnalysis = useTwinStore((s) => s.saveAnalysis);

  const pro = getPro(preferredProId) ?? getPro(defaultProId())!;
  const reference = getReferenceClip(pro.id);

  const userSync =
    result?.userSync ??
    liveUserSync ??
    (skeleton.length ? syncFromSkeleton(skeleton) : undefined);
  const tourSync =
    result?.tourSync ??
    liveTourSync ??
    (userSync ? modelSyncFromUser(userSync) : undefined);

  const applyTourDisplayStyle = useCallback(
    async (src: string, userMeta?: BodyFrameMeta) => {
      try {
        const { crop, sourceW, sourceH } = await detectBodyCropFromUrl(
          src,
          "tour",
        );
        const scale = userMeta
          ? tourMatchScale(userMeta, crop, sourceH, sourceW)
          : 1.6;
        setTourDisplayStyle(cropToVideoStyle(crop, sourceW, sourceH, scale));
      } catch {
        setTourDisplayStyle({ objectFit: "cover", objectPosition: "50% 45%" });
      }
    },
    [],
  );

  const captureReference = useCallback(async () => {
    const ref = getReferenceClip(pro.id);
    if (!ref) return undefined;
    const gen = ++tourLoadGen.current;

    setTourUrl(ref.src);
    setTourFileName(ref.label);
    setUsingReference(true);
    setSyncBusy("Loading Rory…");

    try {
      void applyTourDisplayStyle(ref.src, userFrameMeta);

      const video = await loadVideo(ref.src);
      if (gen !== tourLoadGen.current) return undefined;

      const cap = await captureView(video, "downTheLine", ref.label, {
        handedness,
        style: pro.style ?? TOUR_STYLE,
      });
      if (gen !== tourLoadGen.current) return undefined;

      setRefTourCapture(cap);
      setLiveTourSync(detectSwingSync(cap.samples, cap.duration));
      return cap;
    } catch (e) {
      if (gen === tourLoadGen.current) {
        setError(e instanceof Error ? e.message : "Could not load Rory clip.");
      }
      return undefined;
    } finally {
      if (gen === tourLoadGen.current) setSyncBusy(null);
    }
  }, [pro.id, pro.style, handedness, userFrameMeta, applyTourDisplayStyle]);

  useEffect(() => {
    return () => {
      if (isBlobUrl(userUrl)) URL.revokeObjectURL(userUrl!);
    };
  }, [userUrl]);

  useEffect(() => {
    return () => {
      tourRevokeRef.current?.();
      tourRevokeRef.current = null;
    };
  }, [tourUrl]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const user = await clipObjectUrl("user");
      if (cancelled) {
        if (user?.url) URL.revokeObjectURL(user.url);
        return;
      }
      if (user) {
        setUserUrl(user.url);
        setUserFileName(user.name);
        const row = await loadClip("user");
        if (row) {
          const file = new File([row.blob], row.name, { type: row.blob.type });
          setMyFace(file);
          void captureUserForSync(file);
          try {
            const { crop, sourceW, sourceH } = await detectBodyCropFromUrl(user.url);
            if (!cancelled) {
              const meta: BodyFrameMeta = {
                bodyFill: 1,
                outputW: 540,
                outputH: 720,
                sourceCrop: crop,
                sourceW,
                sourceH,
              };
              setUserFrameMeta(meta);
              setUserDisplayStyle(cropToVideoStyle(crop, sourceW, sourceH));
            }
          } catch {
            /* show uncropped if analysis fails */
          }
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    void captureReference();
  }, [captureReference]);

  function trackUpload(slot: UploadSlot) {
    return (progress: { label: string; percent: number }) => {
      setUploadProgress({
        slot,
        label: progress.label,
        percent: progress.percent,
      });
    };
  }

  async function captureUserForSync(file: File, slot: UploadSlot = "face") {
    setUploadProgress({
      slot,
      label: "Finding takeaway → impact…",
      percent: 96,
    });
    try {
      const { video } = await fileToVideo(file);
      const cap = await captureView(video, "faceOn", file.name, { handedness });
      setLiveUserSync(detectSwingSync(cap.samples, cap.duration));
      return cap;
    } finally {
      /* progress cleared by caller */
    }
  }

  async function prepareUserClip(file: File, slot: UploadSlot) {
    setUploadProgress({ slot, label: "Starting upload…", percent: 0 });
    try {
      return await autoFrameSwingVideo(file, trackUpload(slot));
    } finally {
      /* cleared by caller */
    }
  }

  async function refreshTourDisplay() {
    if (!reference || !tourUrl) return;
    await applyTourDisplayStyle(tourUrl, userFrameMeta);
  }

  async function applyUserFace(file: File) {
    try {
      const { file: f, meta } = await prepareUserClip(file, "face");
      setUploadProgress({ slot: "face", label: "Saving clip…", percent: 95 });
      setUserFrameMeta(meta);
      setUserDisplayStyle(
        cropToVideoStyle(meta.sourceCrop, meta.sourceW, meta.sourceH),
      );
      setMyFace(f);
      const url = URL.createObjectURL(f);
      setUserUrl((prev) => {
        if (isBlobUrl(prev)) URL.revokeObjectURL(prev!);
        return url;
      });
      setUserFileName(f.name);
      await saveClip("user", f);
      await captureUserForSync(f, "face");
      setUploadProgress({ slot: "face", label: "Matching Rory scale…", percent: 98 });
      await refreshTourDisplay();
      setUploadProgress({ slot: "face", label: "Upload complete", percent: 100 });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed.");
      setUploadProgress(null);
    } finally {
      window.setTimeout(() => setUploadProgress(null), 700);
    }
  }

  async function applyUserDtl(file: File) {
    try {
      const { file: f, meta } = await prepareUserClip(file, "dtl");
      setMyDtl(f);
      if (!myFace && !userFileName && !userUrl) {
        const url = URL.createObjectURL(f);
        setUserUrl(url);
        setUserFileName(f.name);
        setUserDisplayStyle(
          cropToVideoStyle(meta.sourceCrop, meta.sourceW, meta.sourceH),
        );
        setUserFrameMeta(meta);
      }
      setUploadProgress({ slot: "dtl", label: "Upload complete", percent: 100 });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed.");
      setUploadProgress(null);
    } finally {
      window.setTimeout(() => setUploadProgress(null), 700);
    }
  }

  function commit(userViews: ViewCapture[], tourViews?: ViewCapture[]) {
    const user = applyHandedness(userViews, handedness);
    const tour = tourViews
      ? applyHandedness(tourViews, handedness, pro.style ?? TOUR_STYLE)
      : undefined;
    const fused = fuseSkeletons(
      user.find((v) => v.view === "faceOn")?.skeleton,
      user.find((v) => v.view === "downTheLine")?.skeleton,
    );
    const analysis = analyzePair({
      userViews: user,
      tourViews: tour,
      proId: pro.id,
      handedness,
      trialLimited: false,
    });
    const thumbsOut = [
      ...user.flatMap((v) => v.thumbs),
      ...(tour?.flatMap((v) => v.thumbs) ?? []),
    ];
    setTourFrames(tour?.[0]?.skeleton);
    setLiveUserSync(analysis.userSync);
    setLiveTourSync(analysis.tourSync);
    const saved = saveAnalysis(analysis, fused, thumbsOut);
    if (!saved.ok) setError(saved.message);
  }

  async function run() {
    setError(null);
    if (!myFace && !myDtl && !userUrl) {
      setError("Upload at least one clip of your own swing.");
      return;
    }
    const urls: string[] = [];
    try {
      const userViews: ViewCapture[] = [];
      if (myFace) {
        setBusy("Reading your face-on clip…");
        await saveClip("user", myFace);
        const { video, url } = await fileToVideo(myFace);
        urls.push(url);
        setUserUrl(url);
        setUserFileName(myFace.name);
        userViews.push(
          await captureView(video, "faceOn", myFace.name, { handedness }),
        );
      } else if (userUrl && userFileName) {
        const video = await loadVideo(userUrl);
        userViews.push(
          await captureView(video, "faceOn", userFileName, { handedness }),
        );
      }
      if (myDtl) {
        setBusy("Reading your down-the-line clip…");
        const { video, url } = await fileToVideo(myDtl);
        urls.push(url);
        if (!myFace) setUserUrl(url);
        userViews.push(
          await captureView(video, "downTheLine", myDtl.name, { handedness }),
        );
      }
      let tourViews: ViewCapture[] | undefined;
      if (refTourCapture) {
        tourViews = [refTourCapture];
      } else {
        const cap = await captureReference();
        if (cap) tourViews = [cap];
      }
      setBusy("Syncing takeaway → impact with Rory…");
      commit(userViews, tourViews);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Compare failed.");
      urls.forEach((u) => URL.revokeObjectURL(u));
    } finally {
      setBusy(null);
    }
  }

  function runSample() {
    setError(null);
    const set = sampleCompareSet(handedness);
    commit(set.user, set.tour);
  }

  async function clearUserFace() {
    if (isBlobUrl(userUrl)) URL.revokeObjectURL(userUrl!);
    try {
      await deleteClip("user");
    } catch {
      /* ignore missing row */
    }
    setMyFace(null);
    setUserUrl(undefined);
    setUserFileName(undefined);
    setLiveUserSync(undefined);
    setUserFrameMeta(undefined);
    setUserDisplayStyle(undefined);
    if (userFaceInputRef.current) userFaceInputRef.current.value = "";
  }

  function clearUserDtl() {
    setMyDtl(null);
    if (userDtlInputRef.current) userDtlInputRef.current.value = "";
  }

  const hasUserFace = Boolean(myFace || userFileName || userUrl);
  const hasUserDtl = Boolean(myDtl);

  return (
    <div className="twin-page">
      <header className="twin-page__head">
        <p className="twin-kicker">Compare</p>
        <h1>You on the left — Rory on the right</h1>
        <p>
          Upload your face-on clip on the left — sky is cut at the driver apex (top of
          backswing), plus floor and sides removed so your body fills the frame. Rory
          loads automatically on the right.
        </p>
      </header>

      <PlayerPicker value={pro.id} onChange={setPreferredPro} />

      <div className="twin-grid2">
        <label
          className={`twin-drop${uploadProgress?.slot === "face" ? " is-uploading" : ""}`}
        >
          <span>Left — your swing (face-on)</span>
          <strong>{myFace?.name || userFileName || "Choose video"}</strong>
          <em>Sky cut at driver apex · floor/sides removed</em>
          {hasUserFace ? (
            <button
              type="button"
              className="twin-drop__remove"
              aria-label="Remove face-on clip"
              onClick={(e) => {
                e.preventDefault();
                void clearUserFace();
              }}
            >
              Remove
            </button>
          ) : null}
          <input
            ref={userFaceInputRef}
            type="file"
            accept="video/*"
            disabled={Boolean(uploadProgress)}
            onChange={(e) => {
              const f = e.target.files?.[0] ?? null;
              if (f) void applyUserFace(f);
            }}
          />
        </label>
        <label
          className={`twin-drop${uploadProgress?.slot === "dtl" ? " is-uploading" : ""}`}
        >
          <span>Your swing — behind (optional)</span>
          <strong>{myDtl ? myDtl.name : "Choose video"}</strong>
          <em>Sky cut at driver apex · floor/sides removed · unlocks 3D</em>
          {hasUserDtl ? (
            <button
              type="button"
              className="twin-drop__remove"
              aria-label="Remove down-the-line clip"
              onClick={(e) => {
                e.preventDefault();
                clearUserDtl();
              }}
            >
              Remove
            </button>
          ) : null}
          <input
            ref={userDtlInputRef}
            type="file"
            accept="video/*"
            disabled={Boolean(uploadProgress)}
            onChange={(e) => {
              const f = e.target.files?.[0] ?? null;
              if (f) void applyUserDtl(f);
            }}
          />
        </label>
      </div>

      {uploadProgress ? (
        <UploadProgressBar
          slot={uploadProgress.slot}
          label={uploadProgress.label}
          percent={uploadProgress.percent}
        />
      ) : null}

      <div className="twin-toolbar">
        <label>
          You play
          <select
            value={handedness}
            onChange={(e) =>
              setHandedness(e.target.value === "left" ? "left" : "right")
            }
          >
            <option value="right">Right-handed</option>
            <option value="left">Left-handed</option>
          </select>
        </label>
        <button
          type="button"
          className="twin-btn"
          onClick={() => void run()}
          disabled={Boolean(busy)}
        >
          {busy ?? "Compare & save"}
        </button>
        <button
          type="button"
          className="twin-btn twin-btn--ghost"
          onClick={runSample}
          disabled={Boolean(busy)}
        >
          Sample pair
        </button>
      </div>
      {reference && usingReference ? (
        <p className="twin-note">
          Right panel: <strong>{reference.label}</strong> from{" "}
          <a href={reference.sourceUrl} target="_blank" rel="noreferrer">
            {reference.sourceName}
          </a>
          . Same style of clip reposted on {reference.instagramHandles.join(", ")}.
          Instagram is not scraped — this is a bundled official excerpt.
        </p>
      ) : null}
      {syncBusy ? <p className="twin-note">{syncBusy}</p> : null}
      {error ? <p className="twin-error">{error}</p> : null}

      <SideBySide
        userUrl={userUrl}
        tourUrl={tourUrl}
        userLabel={myFace?.name || userFileName || "Your swing"}
        tourLabel={tourFileName || pro.name}
        userSync={userSync}
        tourSync={tourSync}
        phaseT={phaseT}
        pro={pro}
        handedness={handedness}
        tourIsReference={usingReference}
        tourVideoStyle={tourDisplayStyle}
        userVideoStyle={userDisplayStyle}
      />

      {userUrl && tourUrl && userSync && tourSync ? (
        <p className="twin-note">
          Press <strong>Play synced swing</strong> — both clips start at takeaway
          and hit impact together.
        </p>
      ) : userUrl && !userSync ? (
        <p className="twin-note">Reading your clip for sync points…</p>
      ) : null}

      {result && skeleton.length ? (
        <PhaseOverlay
          userFrames={skeleton}
          proFrames={tourFrames}
          pro={pro}
          handedness={handedness}
          trialLimited={false}
          onPhase={(_i, t) => setPhaseT(t)}
        />
      ) : null}

      {result ? (
        <section className="twin-result">
          <div className="twin-score">
            <p>Match</p>
            <strong>{result.overall}</strong>
            <span>
              vs {result.proName}
              {result.comparedAgainstClip ? " · real tour clip" : " · player model"}
            </span>
            <em>
              {result.has3d
                ? "3D from face-on + down-the-line"
                : "Add a behind-the-ball clip for 3D"}
            </em>
          </div>
          <Swing3D
            frames={skeleton}
            label={result.has3d ? "Drag to orbit" : "Single-camera preview"}
          />
        </section>
      ) : null}

      {thumbs.length ? (
        <div className="twin-thumbs">
          {thumbs.map((src, i) => (
            <img key={i} src={src} alt="" />
          ))}
        </div>
      ) : null}

      {result ? (
        <>
          <h2>Where you differ</h2>
          <ul className="twin-gaps">
            {result.gaps.map((g) => (
              <li key={g.key} className={`is-${g.severity}`}>
                <p>
                  {g.label}
                  <span>
                    You {g.user} · Them {g.pro}
                  </span>
                </p>
                <p>{g.summary}</p>
                <p className="twin-gaps__drill">Fix: {g.drill}</p>
                <p className="twin-gaps__feel">Feel: {g.feel}</p>
              </li>
            ))}
          </ul>
          <div className="twin-phases twin-phases--fine">
            {(result.finePhaseNotes ?? []).map((p) => (
              <article key={`${p.n}-${p.label}`}>
                <h3>
                  {p.n}. {p.code} · {p.label}
                </h3>
                <p>{p.note}</p>
              </article>
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}
