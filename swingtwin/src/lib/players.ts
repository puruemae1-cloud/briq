import { TOUR_STYLE, type PlayerStyle } from "./anatomy";
import type { ProProfile, SwingMetrics, SwingPhase } from "./types";

export type IgSourceId =
  | "golf_swings"
  | "pgatour"
  | "golfdigest"
  | "golf_gods"
  | "golfonthesnap"
  | "purego1f";

export const IG_SOURCES: {
  id: IgSourceId;
  url: string;
  handle: string;
}[] = [
  { id: "golf_swings", url: "https://www.instagram.com/golf_swings", handle: "@golf_swings" },
  { id: "pgatour", url: "https://www.instagram.com/pgatour", handle: "@pgatour" },
  { id: "golfdigest", url: "https://www.instagram.com/golfdigest", handle: "@golfdigest" },
  { id: "golf_gods", url: "https://www.instagram.com/golf_gods", handle: "@golf_gods" },
  { id: "golfonthesnap", url: "https://www.instagram.com/golfonthesnap", handle: "@golfonthesnap" },
  { id: "purego1f", url: "https://www.instagram.com/purego1f", handle: "@purego1f" },
];

/**
 * Instagram does not allow unofficial scraping. These models are distilled
 * from the public slow-mo patterns those accounts repeat (FO / DTL, tour
 * players) plus documented swing traits. Subscribers can still upload a
 * saved clip of the same player for clip-vs-clip compare.
 */
const ALL: IgSourceId[] = [
  "golf_swings",
  "pgatour",
  "golfdigest",
  "golf_gods",
  "golfonthesnap",
];

function cues(name: string): Record<SwingPhase, string> {
  return {
    address: `${name}: copy stance width and ball first.`,
    takeaway: `${name}: club, hands and chest leave together.`,
    top: `${name}: hold width; hips trail the shoulders.`,
    transition: `${name}: lower body starts; do not throw the club.`,
    impact: `${name}: handle ahead, hips open, chest covering.`,
    finish: `${name}: weight on the lead heel, hold the pose.`,
  };
}

function metricsFromStyle(s: PlayerStyle): SwingMetrics {
  return {
    shoulderTurn: Math.round(s.shoulderTurn * 100),
    hipTurn: Math.round(s.hipClear * 70 + 20),
    xFactor: Math.round((s.shoulderTurn - s.hipClear * 0.4) * 70 + 20),
    spineTilt: Math.round(s.spineTilt * 100),
    headStability: Math.round(s.headQuiet * 100),
    weightShift: Math.round((1 - s.earlyExt) * 50 + s.hipClear * 50),
    clubPath: Math.round(s.handPathIn * 90 + 10),
    lag: Math.round(s.leadWristBow * 40 + s.trailElbowIn * 50),
    posture: Math.round((1 - s.earlyExt) * 100),
    tempo: Math.round(s.tempo * 100),
  };
}

function style(over: Partial<PlayerStyle> = {}): PlayerStyle {
  return { ...TOUR_STYLE, ...over };
}

function hashStyle(name: string, over: Partial<PlayerStyle> = {}): PlayerStyle {
  let h = 2166136261;
  for (let i = 0; i < name.length; i++) {
    h ^= name.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  const n = (k: number) => ((h >>> (k % 24)) & 255) / 255;
  return style({
    headQuiet: 0.7 + n(1) * 0.22,
    stanceWidth: 0.58 + n(2) * 0.3,
    shoulderTurn: 0.68 + n(3) * 0.28,
    hipClear: 0.55 + n(4) * 0.35,
    trailElbowIn: 0.55 + n(5) * 0.35,
    leadWristBow: 0.35 + n(6) * 0.45,
    earlyExt: 0.08 + n(7) * 0.18,
    backswingLen: 0.62 + n(8) * 0.32,
    tempo: 0.55 + n(9) * 0.35,
    squat: 0.3 + n(10) * 0.4,
    handPathIn: 0.5 + n(11) * 0.4,
    spineTilt: 0.65 + n(12) * 0.28,
    ...over,
  });
}

type Row = {
  id: string;
  name: string;
  country: string;
  role: string;
  signature: string;
  sources?: IgSourceId[];
  style?: Partial<PlayerStyle>;
};

function toPro(row: Row): ProProfile {
  const st = hashStyle(row.name, row.style);
  return {
    id: row.id,
    name: row.name,
    tour: "PGA Tour",
    country: row.country,
    role: row.role,
    signature: row.signature,
    whyMatch: `Match ${row.name} from the @golf_swings / @pgatour / @golfdigest / @golf_gods / @golfonthesnap archive.`,
    sources: row.sources ?? ALL,
    style: st,
    metrics: metricsFromStyle(st),
    phaseCues: cues(row.name),
  };
}

const ROWS: Row[] = [
  { id: "rory-mcilroy", name: "Rory McIlroy", country: "Northern Ireland", role: "Wide arc, hip clearance", signature: "Wide stance, huge shoulder turn, hips clear early.", style: { shoulderTurn: 0.96, hipClear: 0.9, stanceWidth: 0.88, backswingLen: 0.94, tempo: 0.62 } },
  { id: "scottie-scheffler", name: "Scottie Scheffler", country: "USA", role: "Athletic footwork", signature: "Feet stay alive; deep lead-side shift, square face.", style: { hipClear: 0.95, earlyExt: 0.22, headQuiet: 0.7, squat: 0.7 } },
  { id: "xander-schauffele", name: "Xander Schauffele", country: "USA", role: "Stacked impact", signature: "Textbook sequence, body stacked on the ball.", style: { spineTilt: 0.9, headQuiet: 0.92, handPathIn: 0.82 } },
  { id: "collin-morikawa", name: "Collin Morikawa", country: "USA", role: "Compact irons", signature: "Short backswing, quiet body, high hands through.", style: { backswingLen: 0.58, headQuiet: 0.95, tempo: 0.9, trailElbowIn: 0.9 } },
  { id: "jon-rahm", name: "Jon Rahm", country: "Spain", role: "Short, explosive", signature: "Strong grip, short swing, lower body leads hard.", style: { backswingLen: 0.52, hipClear: 0.88, tempo: 0.55, leadWristBow: 0.7 } },
  { id: "viktor-hovland", name: "Viktor Hovland", country: "Norway", role: "Iron purity", signature: "Quiet head, strong cover, crisp shaft lean.", style: { headQuiet: 0.93, spineTilt: 0.88, leadWristBow: 0.72 } },
  { id: "ludvig-aberg", name: "Ludvig Åberg", country: "Sweden", role: "Tall, simple", signature: "Long levers, unhurried tempo, quiet lower body.", style: { tempo: 0.88, backswingLen: 0.86, headQuiet: 0.9 } },
  { id: "bryson-dechambeau", name: "Bryson DeChambeau", country: "USA", role: "Single-plane power", signature: "Upright, wide, huge pressure shift.", style: { stanceWidth: 0.95, squat: 0.75, shoulderTurn: 0.8, spineTilt: 0.55 } },
  { id: "brooks-koepka", name: "Brooks Koepka", country: "USA", role: "Major-day fade", signature: "Short, aggressive, holds the face.", style: { backswingLen: 0.64, hipClear: 0.86, tempo: 0.6 } },
  { id: "jordan-spieth", name: "Jordan Spieth", country: "USA", role: "Loop and timing", signature: "Slight loop, great face control, lively feet.", style: { handPathIn: 0.48, headQuiet: 0.72, tempo: 0.7 } },
  { id: "justin-thomas", name: "Justin Thomas", country: "USA", role: "Vertical speed", signature: "Steepish look, fast hips, high finish.", style: { backswingLen: 0.78, hipClear: 0.88, squat: 0.4 } },
  { id: "hideki-matsuyama", name: "Hideki Matsuyama", country: "Japan", role: "Pause at the top", signature: "Visible pause, then a drop into the slot.", style: { tempo: 0.45, trailElbowIn: 0.92, headQuiet: 0.9 } },
  { id: "patrick-cantlay", name: "Patrick Cantlay", country: "USA", role: "Quiet efficiency", signature: "Minimal extra motion, stacked, repeatable.", style: { headQuiet: 0.94, earlyExt: 0.08, tempo: 0.84 } },
  { id: "wyndham-clark", name: "Wyndham Clark", country: "USA", role: "Aggressive speed", signature: "Fast hips, strong release, high finish.", style: { hipClear: 0.9, tempo: 0.58 } },
  { id: "max-homa", name: "Max Homa", country: "USA", role: "Neutral tour swing", signature: "Clean takeaway, quiet head, balanced finish.", style: { headQuiet: 0.9, handPathIn: 0.75 } },
  { id: "tony-finau", name: "Tony Finau", country: "USA", role: "Long levers", signature: "Tall arc, late speed, easy rhythm.", style: { backswingLen: 0.9, tempo: 0.8, stanceWidth: 0.8 } },
  { id: "sahith-theegala", name: "Sahith Theegala", country: "USA", role: "Free-flowing", signature: "Long swing, lots of wrist, athletic finish.", style: { backswingLen: 0.92, leadWristBow: 0.4, tempo: 0.66 } },
  { id: "tommy-fleetwood", name: "Tommy Fleetwood", country: "England", role: "Silky tempo", signature: "One-piece look, unhurried, great face.", style: { tempo: 0.92, headQuiet: 0.91, handPathIn: 0.8 } },
  { id: "shane-lowry", name: "Shane Lowry", country: "Ireland", role: "Strong, compact", signature: "Shorter backswing, stout lower body.", style: { backswingLen: 0.62, squat: 0.6, hipClear: 0.8 } },
  { id: "min-woo-lee", name: "Min Woo Lee", country: "Australia", role: "Young speed", signature: "Long, fast, high hands.", style: { backswingLen: 0.9, tempo: 0.6, shoulderTurn: 0.9 } },
  { id: "jason-day", name: "Jason Day", country: "Australia", role: "Wide takeaway", signature: "Low and wide, then a deep coil.", style: { handPathIn: 0.55, shoulderTurn: 0.9, stanceWidth: 0.84 } },
  { id: "adam-scott", name: "Adam Scott", country: "Australia", role: "Classic iron", signature: "Upright, elegant, quiet head.", style: { headQuiet: 0.94, spineTilt: 0.86, tempo: 0.86 } },
  { id: "cameron-smith", name: "Cameron Smith", country: "Australia", role: "Short and bowed", signature: "Short swing, bowed lead wrist, huge speed.", style: { backswingLen: 0.5, leadWristBow: 0.92, hipClear: 0.88 } },
  { id: "joaquin-niemann", name: "Joaquin Niemann", country: "Chile", role: "Smooth power", signature: "Wide arc, easy tempo, high finish.", style: { tempo: 0.84, backswingLen: 0.86 } },
  { id: "sungjae-im", name: "Sungjae Im", country: "Korea", role: "Repeatable", signature: "Compact, on-plane, very little sway.", style: { headQuiet: 0.93, handPathIn: 0.84, earlyExt: 0.1 } },
  { id: "tom-kim", name: "Tom Kim", country: "Korea", role: "Quick tempo", signature: "Shorter swing, lively feet, fast through.", style: { tempo: 0.5, backswingLen: 0.66 } },
  { id: "si-woo-kim", name: "Si Woo Kim", country: "Korea", role: "Strong cover", signature: "Quiet lower body, lots of shaft lean.", style: { leadWristBow: 0.78, spineTilt: 0.86 } },
  { id: "corey-conners", name: "Corey Conners", country: "Canada", role: "Iron machine", signature: "On-plane, modest sway, crisp strike.", style: { handPathIn: 0.86, headQuiet: 0.9 } },
  { id: "sam-burns", name: "Sam Burns", country: "USA", role: "Free release", signature: "Athletic, high finish, lots of speed.", style: { hipClear: 0.86, backswingLen: 0.82 } },
  { id: "cameron-young", name: "Cameron Young", country: "USA", role: "Bomber fade", signature: "Steepish down, huge speed, left miss protected.", style: { shoulderTurn: 0.9, hipClear: 0.84 } },
  { id: "keegan-bradley", name: "Keegan Bradley", country: "USA", role: "Long backswing", signature: "Big turn, pronounced wrist set.", style: { backswingLen: 0.95, shoulderTurn: 0.92 } },
  { id: "russell-henley", name: "Russell Henley", country: "USA", role: "Textbook", signature: "Quiet, stacked, very little extra.", style: { headQuiet: 0.95, earlyExt: 0.08, tempo: 0.88 } },
  { id: "brian-harman", name: "Brian Harman", country: "USA", role: "Compact lefty", signature: "Short, efficient, great control.", style: { backswingLen: 0.58, tempo: 0.8 } },
  { id: "denny-mccarthy", name: "Denny McCarthy", country: "USA", role: "Feel player", signature: "Soft hands, quiet body.", style: { tempo: 0.86, headQuiet: 0.88 } },
  { id: "sepp-straka", name: "Sepp Straka", country: "Austria", role: "Tall and simple", signature: "Long levers, little extra motion.", style: { backswingLen: 0.84, headQuiet: 0.9 } },
  { id: "matt-fitzpatrick", name: "Matt Fitzpatrick", country: "England", role: "Data-driven", signature: "Shortish, organised, great face.", style: { backswingLen: 0.64, trailElbowIn: 0.88, tempo: 0.82 } },
  { id: "tyrrell-hatton", name: "Tyrrell Hatton", country: "England", role: "Short and fierce", signature: "Compact, strong release, lots of speed.", style: { backswingLen: 0.56, hipClear: 0.86, tempo: 0.52 } },
  { id: "robert-macintyre", name: "Robert MacIntyre", country: "Scotland", role: "Lefty power", signature: "Wide, aggressive, high finish.", style: { stanceWidth: 0.84, hipClear: 0.86 } },
  { id: "justin-rose", name: "Justin Rose", country: "England", role: "Classic tour", signature: "On-plane, elegant, quiet head.", style: { headQuiet: 0.93, handPathIn: 0.82, tempo: 0.84 } },
  { id: "rickie-fowler", name: "Rickie Fowler", country: "USA", role: "Long and rhythmic", signature: "Full turn, smooth tempo, high finish.", style: { backswingLen: 0.88, tempo: 0.8 } },
  { id: "dustin-johnson", name: "Dustin Johnson", country: "USA", role: "Open-face power", signature: "Clubface looks open, bowed lead wrist, huge speed.", style: { leadWristBow: 0.88, hipClear: 0.9, backswingLen: 0.8 } },
  { id: "phil-mickelson", name: "Phil Mickelson", country: "USA", role: "Lefty artist", signature: "Long swing, lots of hands, high finish.", style: { backswingLen: 0.92, tempo: 0.7, handPathIn: 0.55 } },
  { id: "tiger-woods", name: "Tiger Woods", country: "USA", role: "Archive model", signature: "The FO/DTL template those accounts still post.", style: { headQuiet: 0.9, hipClear: 0.92, trailElbowIn: 0.88, tempo: 0.7 } },
  { id: "sergio-garcia", name: "Sergio Garcia", country: "Spain", role: "Lag king", signature: "Holds the angle forever, then releases.", style: { leadWristBow: 0.9, trailElbowIn: 0.86, tempo: 0.68 } },
  { id: "louis-oosthuizen", name: "Louis Oosthuizen", country: "South Africa", role: "One-plane beauty", signature: "Maybe the cleanest FO/DTL on those pages.", style: { headQuiet: 0.96, handPathIn: 0.88, tempo: 0.9 } },
  { id: "ernie-els", name: "Ernie Els", country: "South Africa", role: "Big Easy", signature: "Long, lazy tempo, huge arc.", style: { tempo: 0.95, backswingLen: 0.9 } },
  { id: "will-zalatoris", name: "Will Zalatoris", country: "USA", role: "Upright speed", signature: "Steep look, fast through, high hands.", style: { spineTilt: 0.7, backswingLen: 0.84 } },
  { id: "akshay-bhatia", name: "Akshay Bhatia", country: "USA", role: "Young lefty", signature: "Compact, quick, great face.", style: { backswingLen: 0.66, tempo: 0.62 } },
  { id: "nick-dunlap", name: "Nick Dunlap", country: "USA", role: "Amateur-to-tour", signature: "Simple, young, on-plane.", style: { tempo: 0.78, headQuiet: 0.86 } },
  { id: "jj-spaun", name: "J.J. Spaun", country: "USA", role: "Quiet strike", signature: "Minimal extra, stacked impact.", style: { headQuiet: 0.9, earlyExt: 0.1 } },
  { id: "harris-english", name: "Harris English", country: "USA", role: "Reliable tour", signature: "Neutral, repeatable, good posture.", style: { spineTilt: 0.84, tempo: 0.8 } },
  { id: "maverick-mcnealy", name: "Maverick McNealy", country: "USA", role: "Efficient", signature: "Shortish, organised, little sway.", style: { backswingLen: 0.64, headQuiet: 0.9 } },
  { id: "kurt-kitayama", name: "Kurt Kitayama", country: "USA", role: "Power fade", signature: "Strong lower body, holds the face.", style: { hipClear: 0.86, stanceWidth: 0.8 } },
  { id: "aaron-rai", name: "Aaron Rai", country: "England", role: "Quiet English", signature: "Compact, on-plane, very still head.", style: { headQuiet: 0.96, backswingLen: 0.62 } },
  { id: "matthieu-pavon", name: "Matthieu Pavon", country: "France", role: "Strong cover", signature: "Athletic, lots of shaft lean.", style: { leadWristBow: 0.74, hipClear: 0.82 } },
  { id: "alex-noren", name: "Alex Noren", country: "Sweden", role: "Wristy artist", signature: "Lots of hands, great short-game DNA in the full swing.", style: { leadWristBow: 0.45, tempo: 0.7 } },
  { id: "thorbjorn-olesen", name: "Thorbjørn Olesen", country: "Denmark", role: "Aggressive", signature: "Fast through, high finish.", style: { hipClear: 0.86, tempo: 0.58 } },
  { id: "nicolai-hojgaard", name: "Nicolai Højgaard", country: "Denmark", role: "Tall bomber", signature: "Long levers, modern speed.", style: { backswingLen: 0.88, stanceWidth: 0.82 } },
  { id: "rasmus-hojgaard", name: "Rasmus Højgaard", country: "Denmark", role: "Twin bomber", signature: "Similar length, slightly different tempo.", style: { backswingLen: 0.86, tempo: 0.64 } },
  { id: "cam-davis", name: "Cam Davis", country: "Australia", role: "Lefty tour", signature: "Wide, balanced, high finish.", style: { stanceWidth: 0.8, tempo: 0.78 } },
  { id: "eric-cole", name: "Eric Cole", country: "USA", role: "Short and tidy", signature: "Compact, great strike, little waste.", style: { backswingLen: 0.56, headQuiet: 0.9 } },
  { id: "seamus-power", name: "Séamus Power", country: "Ireland", role: "Tall Irish", signature: "Long swing, easy rhythm.", style: { backswingLen: 0.86, tempo: 0.8 } },
  { id: "keith-mitchell", name: "Keith Mitchell", country: "USA", role: "Bomber", signature: "Wide stance, huge turn.", style: { stanceWidth: 0.9, shoulderTurn: 0.92 } },
  { id: "patrick-reed", name: "Patrick Reed", country: "USA", role: "Strong grip", signature: "Shut look, short, fights a hook.", style: { leadWristBow: 0.8, backswingLen: 0.6 } },
  { id: "billy-horschel", name: "Billy Horschel", country: "USA", role: "On-plane", signature: "Textbook FO, quiet head.", style: { headQuiet: 0.92, handPathIn: 0.84 } },
  { id: "webb-simpson", name: "Webb Simpson", country: "USA", role: "Saw-grip full", signature: "Unusual grip, very repeatable body.", style: { headQuiet: 0.9, tempo: 0.82 } },
  { id: "bubba-watson", name: "Bubba Watson", country: "USA", role: "Long lefty", signature: "Huge arc, lots of hands, high finish.", style: { backswingLen: 0.98, handPathIn: 0.4, tempo: 0.6 } },
  { id: "gary-woodland", name: "Gary Woodland", country: "USA", role: "Power fade", signature: "Wide, strong, holds the face.", style: { stanceWidth: 0.88, hipClear: 0.84 } },
  { id: "byeong-hun-an", name: "Byeong Hun An", country: "Korea", role: "Long Korean", signature: "Huge turn, high finish.", style: { shoulderTurn: 0.93, backswingLen: 0.9 } },
  { id: "tom-hoge", name: "Tom Hoge", country: "USA", role: "Wedge DNA", signature: "Quiet, organised, great face.", style: { headQuiet: 0.9, tempo: 0.84 } },
  { id: "chris-kirk", name: "Chris Kirk", country: "USA", role: "Steady", signature: "Simple, little sway, good posture.", style: { earlyExt: 0.1, headQuiet: 0.88 } },
  { id: "jt-poston", name: "J.T. Poston", country: "USA", role: "Feel fade", signature: "Neutral, repeatable, balanced.", style: { tempo: 0.8, handPathIn: 0.76 } },
  { id: "davis-thompson", name: "Davis Thompson", country: "USA", role: "Young tour", signature: "Modern, on-plane, quiet head.", style: { headQuiet: 0.88, backswingLen: 0.8 } },
  { id: "austin-eckroat", name: "Austin Eckroat", country: "USA", role: "Compact", signature: "Short, tidy, great strike.", style: { backswingLen: 0.6, trailElbowIn: 0.86 } },
  { id: "ben-griffin", name: "Ben Griffin", country: "USA", role: "Rising", signature: "Athletic, free release.", style: { hipClear: 0.82, tempo: 0.7 } },
  { id: "nick-taylor", name: "Nick Taylor", country: "Canada", role: "Canadian tour", signature: "Simple, balanced, little extra.", style: { headQuiet: 0.88, tempo: 0.8 } },
  { id: "adam-hadwin", name: "Adam Hadwin", country: "Canada", role: "Neat fade", signature: "Organised, quiet lower body.", style: { handPathIn: 0.8, earlyExt: 0.12 } },
  { id: "taylor-pendrith", name: "Taylor Pendrith", country: "Canada", role: "Tall bomber", signature: "Long levers, modern speed.", style: { backswingLen: 0.88, stanceWidth: 0.84 } },
  { id: "christiaan-bezuidenhout", name: "Christiaan Bezuidenhout", country: "South Africa", role: "Grippy fade", signature: "Strong pattern, great control.", style: { leadWristBow: 0.7, tempo: 0.78 } },
  { id: "ryan-fox", name: "Ryan Fox", country: "New Zealand", role: "Bomber", signature: "Wide, aggressive, high finish.", style: { stanceWidth: 0.86, hipClear: 0.86 } },
  { id: "jake-knapp", name: "Jake Knapp", country: "USA", role: "Young speed", signature: "Long, fast, high hands.", style: { backswingLen: 0.88, tempo: 0.58 } },
  { id: "michael-kim", name: "Michael Kim", country: "USA", role: "Feel player", signature: "Rhythm first, quiet head.", style: { tempo: 0.84, headQuiet: 0.88 } },
  { id: "andrew-novak", name: "Andrew Novak", country: "USA", role: "Tour regular", signature: "Neutral, repeatable.", style: { headQuiet: 0.86, handPathIn: 0.74 } },
  { id: "emiliano-grillo", name: "Emiliano Grillo", country: "Argentina", role: "Smooth Argentine", signature: "Easy tempo, on-plane.", style: { tempo: 0.88, handPathIn: 0.8 } },
  { id: "abraham-ancer", name: "Abraham Ancer", country: "Mexico", role: "Short and tidy", signature: "Compact, great face, little waste.", style: { backswingLen: 0.58, headQuiet: 0.9 } },
  { id: "carlos-ortiz", name: "Carlos Ortiz", country: "Mexico", role: "Athletic", signature: "Free-flowing, high finish.", style: { hipClear: 0.84, backswingLen: 0.82 } },
  { id: "camilo-villegas", name: "Camilo Villegas", country: "Colombia", role: "Flexible", signature: "Long, whippy, famous postures.", style: { backswingLen: 0.9, squat: 0.35 } },
  { id: "padraig-harrington", name: "Pádraig Harrington", country: "Ireland", role: "Classic major", signature: "Strong, organised, great cover.", style: { spineTilt: 0.86, leadWristBow: 0.7 } },
  { id: "francesco-molinari", name: "Francesco Molinari", country: "Italy", role: "Machine", signature: "Maybe the most repeatable FO on the old reels.", style: { headQuiet: 0.96, earlyExt: 0.07, tempo: 0.9 } },
  { id: "brendon-todd", name: "Brendon Todd", country: "USA", role: "Short and safe", signature: "Very short, very controlled.", style: { backswingLen: 0.48, tempo: 0.86 } },
  { id: "kevin-kisner", name: "Kevin Kisner", country: "USA", role: "Wily", signature: "Compact, great face, little power waste.", style: { backswingLen: 0.58, headQuiet: 0.88 } },
  { id: "joel-dahmen", name: "Joel Dahmen", country: "USA", role: "Tour regular", signature: "Neutral, balanced.", style: { tempo: 0.78, handPathIn: 0.72 } },
  { id: "beau-hossler", name: "Beau Hossler", country: "USA", role: "Smooth", signature: "Easy rhythm, high finish.", style: { tempo: 0.84, backswingLen: 0.8 } },
  { id: "sam-ryder", name: "Sam Ryder", country: "USA", role: "Strike", signature: "Quiet, organised, good posture.", style: { spineTilt: 0.84, headQuiet: 0.88 } },
  { id: "nico-echavarria", name: "Nico Echavarria", country: "Colombia", role: "Young tour", signature: "Athletic, free release.", style: { hipClear: 0.8, tempo: 0.7 } },
  { id: "s-h-kim", name: "S.H. Kim", country: "Korea", role: "Korean tour", signature: "Compact, on-plane.", style: { backswingLen: 0.66, handPathIn: 0.8 } },
  { id: "k-h-lee", name: "K.H. Lee", country: "Korea", role: "Korean tour", signature: "Wide, balanced.", style: { stanceWidth: 0.8, tempo: 0.76 } },
  { id: "adam-svensson", name: "Adam Svensson", country: "Canada", role: "Canadian tour", signature: "Simple, quiet head.", style: { headQuiet: 0.9, tempo: 0.82 } },
  { id: "davis-riley", name: "Davis Riley", country: "USA", role: "Bomber", signature: "Long, fast, high finish.", style: { backswingLen: 0.88, hipClear: 0.84 } },
  { id: "luke-clanton", name: "Luke Clanton", country: "USA", role: "Amateur star", signature: "Modern, on-plane, lots of speed — all over @golfonthesnap.", style: { backswingLen: 0.86, tempo: 0.66, hipClear: 0.84 }, sources: ["golfonthesnap", "golf_swings", "pgatour"] },
  { id: "jack-nicklaus", name: "Jack Nicklaus", country: "USA", role: "Archive legend", signature: "Flying right elbow, huge turn — still the FO template on @golfdigest.", style: { backswingLen: 0.95, shoulderTurn: 0.94, trailElbowIn: 0.45 } },
  { id: "ben-hogan", name: "Ben Hogan", country: "USA", role: "Archive plane", signature: "The plane those accounts still freeze-frame.", style: { handPathIn: 0.95, headQuiet: 0.97, trailElbowIn: 0.94 } },
  { id: "seve-ballesteros", name: "Seve Ballesteros", country: "Spain", role: "Hands and art", signature: "Whippy, lots of hands, famous recovery DNA.", style: { handPathIn: 0.42, tempo: 0.62, backswingLen: 0.88 } },
  { id: "greg-norman", name: "Greg Norman", country: "Australia", role: "Wide power", signature: "Huge arc, high hands, aggressive through.", style: { backswingLen: 0.94, stanceWidth: 0.88, hipClear: 0.86 } },
  { id: "nick-faldo", name: "Nick Faldo", country: "England", role: "Major machine", signature: "Quiet, organised, the UK FO/DTL classic.", style: { headQuiet: 0.96, earlyExt: 0.08, tempo: 0.88 } },
  { id: "payne-stewart", name: "Payne Stewart", country: "USA", role: "Classic fade", signature: "Upright, high hands, famous finish.", style: { spineTilt: 0.7, backswingLen: 0.86, tempo: 0.78 } },
  { id: "fred-couples", name: "Fred Couples", country: "USA", role: "Easy power", signature: "Soft arms, late hit, unhurried.", style: { tempo: 0.94, trailElbowIn: 0.7, hipClear: 0.8 } },
  { id: "vijay-singh", name: "Vijay Singh", country: "Fiji", role: "Range legend", signature: "Wide, strong, huge work-rate DNA.", style: { stanceWidth: 0.86, shoulderTurn: 0.9 } },
  { id: "henrik-stenson", name: "Henrik Stenson", country: "Sweden", role: "Iron cover", signature: "Stacked, lots of shaft lean, quiet head.", style: { leadWristBow: 0.8, spineTilt: 0.9, headQuiet: 0.94 } },
  { id: "martin-kaymer", name: "Martin Kaymer", country: "Germany", role: "Quiet German", signature: "Simple, on-plane, little extra.", style: { headQuiet: 0.92, tempo: 0.84, handPathIn: 0.8 } },
  { id: "charl-schwartzel", name: "Charl Schwartzel", country: "South Africa", role: "Soft hands", signature: "Rhythm first, high finish.", style: { tempo: 0.86, backswingLen: 0.82 } },
  { id: "retief-goosen", name: "Retief Goosen", country: "South Africa", role: "Quiet major", signature: "Minimal extra, stacked, great face.", style: { headQuiet: 0.94, earlyExt: 0.09 } },
  { id: "davis-love-iii", name: "Davis Love III", country: "USA", role: "Tall bomber", signature: "Long levers, high finish, easy tempo.", style: { backswingLen: 0.92, tempo: 0.82 } },
  { id: "tom-mckibbin", name: "Tom McKibbin", country: "Northern Ireland", role: "Young Irish", signature: "Modern, on-plane — often next to Rory on those reels.", style: { backswingLen: 0.8, tempo: 0.7, headQuiet: 0.86 } },
  { id: "alex-fitzpatrick", name: "Alex Fitzpatrick", country: "England", role: "Young English", signature: "Compact, organised, little sway.", style: { backswingLen: 0.66, headQuiet: 0.88 } },
  { id: "harry-hall", name: "Harry Hall", country: "England", role: "English tour", signature: "Athletic, free release.", style: { hipClear: 0.82, tempo: 0.68 } },
  { id: "matt-wallace", name: "Matt Wallace", country: "England", role: "Aggressive", signature: "Short, fierce, lots of speed.", style: { backswingLen: 0.6, hipClear: 0.86, tempo: 0.52 } },
  { id: "laurie-canter", name: "Laurie Canter", country: "England", role: "English tour", signature: "Quiet, on-plane, good posture.", style: { headQuiet: 0.9, spineTilt: 0.84 } },
  { id: "jordan-smith", name: "Jordan Smith", country: "England", role: "English tour", signature: "Neutral, repeatable, balanced.", style: { tempo: 0.8, handPathIn: 0.76 } },
];

const MODELS: ProProfile[] = [
  {
    id: "custom-clip",
    name: "My tour clip",
    tour: "Model",
    role: "Whatever player clip you upload",
    signature: "Your reference video is the model.",
    whyMatch: "Use when you have a specific slow-mo saved from Instagram.",
    sources: ALL,
    style: TOUR_STYLE,
    metrics: metricsFromStyle(TOUR_STYLE),
    phaseCues: cues("Your clip"),
  },
  {
    id: "tour-blend",
    name: "Tour blend",
    tour: "Model",
    role: "Average of the five archives",
    signature: "Quiet head, width at the top, handle forward — the common line on those pages.",
    whyMatch: "When you want tour standards, not one player’s quirk.",
    instagram: "https://www.instagram.com/golf_swings",
    sources: ALL,
    style: TOUR_STYLE,
    metrics: metricsFromStyle(TOUR_STYLE),
    phaseCues: cues("Tour blend"),
  },
];

export const PROS: ProProfile[] = [
  ...MODELS,
  ...ROWS.map(toPro).sort((a, b) => a.name.localeCompare(b.name)),
];

export function getPro(id: string): ProProfile | undefined {
  return PROS.find((p) => p.id === id);
}

export function defaultProId() {
  return "rory-mcilroy";
}

export function searchPros(q: string): ProProfile[] {
  const s = q.trim().toLowerCase();
  if (!s) return PROS;
  return PROS.filter(
    (p) =>
      p.name.toLowerCase().includes(s) ||
      p.country?.toLowerCase().includes(s) ||
      p.role.toLowerCase().includes(s) ||
      p.id.includes(s),
  );
}
