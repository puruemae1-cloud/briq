"use client";

import { useId, useState } from "react";
import type { ShoeSizeChart } from "@/data/bb/bb-shoe-size-charts";

export function SizeChartControl({ chart }: { chart: ShoeSizeChart }) {
  const [open, setOpen] = useState(false);
  const titleId = useId();

  return (
    <div className="size-chart">
      <button
        type="button"
        className="size-chart__trigger"
        onClick={() => setOpen(true)}
      >
        사이즈 차트 보기
      </button>

      {open ? (
        <div
          className="size-chart-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby={titleId}
          onClick={() => setOpen(false)}
        >
          <div
            className="size-chart-modal__panel"
            onClick={(e) => e.stopPropagation()}
          >
            <header className="size-chart-modal__head">
              <div>
                <p className="size-chart-modal__eyebrow">Size Guide</p>
                <h2 id={titleId}>{chart.titleKo}</h2>
              </div>
              <button
                type="button"
                className="size-chart-modal__close"
                aria-label="닫기"
                onClick={() => setOpen(false)}
              >
                ×
              </button>
            </header>
            <p className="size-chart-modal__note">{chart.noteKo}</p>
            <div className="size-chart-modal__table-wrap">
              <table className="size-chart-table">
                <thead>
                  <tr>
                    {chart.headers.map((h) => (
                      <th key={h} scope="col">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {chart.rows.map((row) => (
                    <tr key={row.join("-")}>
                      {row.map((cell, i) => (
                        <td key={`${row[0]}-${i}`}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button
              type="button"
              className="btn btn-solid size-chart-modal__done"
              onClick={() => setOpen(false)}
            >
              확인
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
