"use client";

import { useEffect, useId, useState } from "react";
import { formatKrw } from "@/data/products";
import { CW_BRACELET_RESIZE_FEE } from "@/data/cw-twelve-picnmix";

type BraceletResizeConfig = {
  feeKrw: number;
  sizesCm: string[];
};

export function BraceletResizeControls({
  config,
  value,
  onChange,
  idPrefix = "bracelet",
}: {
  config: BraceletResizeConfig;
  value: string;
  onChange: (next: string) => void;
  idPrefix?: string;
}) {
  const [open, setOpen] = useState(false);
  const titleId = useId();
  const fee = config.feeKrw || CW_BRACELET_RESIZE_FEE;
  const charged = value !== "no";

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open]);

  return (
    <div className="bracelet-resize">
      <div className="bracelet-resize__head">
        <label className="bracelet-resize__label" htmlFor={`${idPrefix}-select`}>
          브레이슬릿 리사이즈
          <span className="bracelet-resize__fee">+{formatKrw(fee)}</span>
        </label>
        <button
          type="button"
          className="bracelet-resize__measure"
          onClick={() => setOpen(true)}
        >
          손목 사이즈 재기
        </button>
      </div>

      <select
        id={`${idPrefix}-select`}
        className="bracelet-resize__select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="no">No — 리사이즈 없음</option>
        {config.sizesCm.map((cm) => (
          <option key={cm} value={cm}>
            {cm}cm (+{formatKrw(fee)})
          </option>
        ))}
      </select>

      {charged ? (
        <p className="bracelet-resize__note">
          선택하신 손목 사이즈로 브레이슬릿을 맞춰 드리며, {formatKrw(fee)}이
          추가됩니다.
        </p>
      ) : (
        <p className="bracelet-resize__note">
          기본 사이즈로 제공됩니다. cm를 선택하면 리사이즈 비용이 추가됩니다.
        </p>
      )}

      {open ? (
        <div
          className="wrist-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby={titleId}
          onClick={() => setOpen(false)}
        >
          <div
            className="wrist-modal__panel"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id={titleId}>손목 사이즈 재기</h2>
            <p>
              새 시계의 브레이슬릿을 손목에 딱 맞게 맞춰 드릴 수 있습니다.
              아래 드롭다운에서 손목 둘레를 알려주시면 저희가 리사이즈를
              진행합니다.
            </p>
            <p>
              <strong>손목 사이즈가 확실하지 않으신가요? 걱정 마세요. 이렇게 확인해 보세요.</strong>
            </p>
            <ol>
              <li>종이나 실을 손목에 둘러 주세요.</li>
              <li>겹치는 지점을 펜으로 표시하세요.</li>
              <li>표시한 지점까지의 길이를 자로 재세요.</li>
              <li>
                ‘브레이슬릿 리사이즈’에서 측정한 손목 사이즈를 선택하세요.
              </li>
            </ol>
            <button
              type="button"
              className="btn btn-solid"
              onClick={() => setOpen(false)}
            >
              닫기
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
