/**
 * Christopher Ward English → Korean display names.
 * Keep model codes (C60, C63, GMT, 300, Ti, Mk …) as-is; translate model words.
 */

const PHRASES: Array<[RegExp, string]> = [
  [/Black Shadow/gi, "블랙 섀도우"],
  [/Sapphire Edge/gi, "사파이어 엣지"],
  [/Super Compressor/gi, "슈퍼 컴프레서"],
  [/Pic'?n'?Mix/gi, "픽앤믹스"],
  [/Bel Canto/gi, "벨 칸토"],
  [/Jump Hour/gi, "점프아워"],
  [/Light Catcher|Light-Catcher/gi, "라이트캐처"],
  [/Full Skeleton/gi, "풀 스켈레톤"],
  [/Open Heart/gi, "오픈하트"],
  [/Power Reserve/gi, "파워리저브"],
  [/Grand Malvern/gi, "그랜드 맬번"],
  [/Sea Timer|Seatimer/gi, "시타이머"],
  [/Elite GMT/gi, "엘리트 GMT"],
  [/Nearly New/gi, "니얼리 뉴"],
  [/Fine Italian/gi, "파인 이탈리안"],
];

const WORDS: Array<[RegExp, string]> = [
  [/\bTrident\b/gi, "트라이던트"],
  [/\bBronze\b/gi, "브론즈"],
  [/\bSealander\b/gi, "실랜더"],
  [/\bTwelve\b/gi, "트웰브"],
  [/\bMoonphase\b/gi, "문페이즈"],
  [/\bAquitaine\b/gi, "아키텐"],
  [/\bSandhurst\b/gi, "샌드허스트"],
  [/\bAtoll\b/gi, "아톨"],
  [/\bLumière|Lumiere\b/gi, "뤼미에르"],
  [/\bReef\b/gi, "리프"],
  [/\bPro\b/gi, "프로"],
  [/\bAutomatic\b/gi, "오토매틱"],
  [/\bChronograph\b/gi, "크로노그래프"],
  [/\bClassic\b/gi, "클래식"],
  [/\bExtreme\b/gi, "익스트림"],
  [/\bSeries\b/gi, "시리즈"],
  [/\bTitanium\b/gi, "티타늄"],
  [/\bCeramic\b/gi, "세라믹"],
  [/\bSkeleton\b/gi, "스켈레톤"],
  [/\bLimited\b/gi, "리미티드"],
  [/\bEdition\b/gi, "에디션"],
  [/\bDive\b/gi, "다이브"],
  [/\bField\b/gi, "필드"],
  [/\bMilitary\b/gi, "밀리터리"],
  [/\bBracelet\b/gi, "브레이슬릿"],
  [/\bLeather\b/gi, "가죽"],
  [/\bRubber\b/gi, "러버"],
  [/\bStrap\b/gi, "스트랩"],
  [/\bHybrid\b/gi, "하이브리드"],
  [/\bAquaflex\b/gi, "아쿠아플렉스"],
  [/\bConsort\b/gi, "콘소트"],
  [/\bBader\b/gi, "베이더"],
  [/\bVintage\b/gi, "빈티지"],
  [/\bOak\b/gi, "오크"],
  [/\bCamel\b/gi, "카멜"],
  [/\bTobacco\b/gi, "토바코"],
  [/\bBlack\b/gi, "블랙"],
  [/\bWhite\b/gi, "화이트"],
  [/\bBlue\b/gi, "블루"],
  [/\bGreen\b/gi, "그린"],
  [/\bOrange\b/gi, "오렌지"],
  [/\bSilver\b/gi, "실버"],
  [/\bGold\b/gi, "골드"],
  [/\bGrey|Gray\b/gi, "그레이"],
  [/\bRed\b/gi, "레드"],
  [/\bYellow\b/gi, "옐로우"],
  [/\bBrown\b/gi, "브라운"],
  [/\bPink\b/gi, "핑크"],
  [/\bPurple\b/gi, "퍼플"],
  [/\bSky\b/gi, "스카이"],
  [/\bTide\b/gi, "타이드"],
  [/\bThe\b/g, ""],
];

/** Translate CW product / option labels to natural Korean while keeping codes. */
export function cwNameToKo(input: string): string {
  let s = input.trim();
  for (const [re, rep] of PHRASES) s = s.replace(re, rep);
  for (const [re, rep] of WORDS) s = s.replace(re, rep);
  s = s.replace(/\s{2,}/g, " ").replace(/\s+\/\s+/g, " / ").trim();
  s = s.replace(/^·\s*|·$/g, "").trim();
  return s || input;
}

/** Build card title: model code kept, Korean descriptors. */
export function cwProductTitleKo(nameEn: string, subtitleEn?: string): string {
  const title = cwNameToKo(nameEn);
  if (!subtitleEn?.trim()) return title;
  const sub = cwNameToKo(subtitleEn);
  if (!sub || title.includes(sub)) return title;
  return `${title} · ${sub}`;
}
