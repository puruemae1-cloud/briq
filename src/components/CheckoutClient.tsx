"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { clearCart } from "@/app/cart/actions";
import { formatKrw } from "@/data/products";
import type { CartItem } from "@/lib/cart-server";
import { usePurchases } from "@/lib/purchase-store";
import {
  paymentMethods,
  requestPayment,
  type PaymentMethod,
} from "@/lib/payments";
import {
  isValidCustomsCode,
  loadCheckoutProfile,
  normalizeCustomsCode,
  saveCheckoutProfile,
} from "@/lib/checkout-profile";
import { useAuthStore } from "@/lib/auth-store";
import { useCouponStore } from "@/lib/coupon-store";
import { useOrderStore } from "@/lib/order-store";

type DaumPostcodeData = {
  zonecode: string;
  address: string;
  roadAddress: string;
  jibunAddress: string;
  userSelectedType: "R" | "J";
  buildingName: string;
  apartment: string;
  bname: string;
};

declare global {
  interface Window {
    daum?: {
      Postcode: new (options: {
        oncomplete: (data: DaumPostcodeData) => void;
        onclose?: (state: string) => void;
        width?: string | number;
        height?: string | number;
      }) => { open: () => void; embed: (el: HTMLElement) => void };
    };
  }
}

/** Digits after 010-, formatted as ####-#### */
function formatPhoneTail(raw: string) {
  const digits = raw.replace(/\D/g, "").slice(0, 8);
  if (digits.length <= 4) return digits;
  return `${digits.slice(0, 4)}-${digits.slice(4)}`;
}

const PHONE_RE = /^010-\d{4}-\d{4}$/;

function loadDaumPostcode(): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  if (window.daum?.Postcode) return Promise.resolve();

  const existing = document.querySelector<HTMLScriptElement>(
    'script[data-daum-postcode="true"]',
  );
  if (existing) {
    return new Promise((resolve, reject) => {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () =>
        reject(new Error("주소 검색 스크립트를 불러오지 못했습니다.")),
      );
    });
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src =
      "//t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js";
    script.async = true;
    script.dataset.daumPostcode = "true";
    script.onload = () => resolve();
    script.onerror = () =>
      reject(new Error("주소 검색 스크립트를 불러오지 못했습니다."));
    document.head.appendChild(script);
  });
}

export function CheckoutClient({ items }: { items: CartItem[] }) {
  const router = useRouter();
  const recordPurchase = usePurchases((s) => s.record);
  const user = useAuthStore((s) => s.currentUser());
  const updateProfile = useAuthStore((s) => s.updateProfile);
  const addOrder = useOrderStore((s) => s.addOrder);
  const coupons = useCouponStore((s) => s.coupons);
  const markCouponUsed = useCouponStore((s) => s.markUsed);
  const detailRef = useRef<HTMLInputElement>(null);
  const subtotal = items.reduce((sum, i) => {
    const unit = i.variant?.price ?? i.product.price;
    return sum + unit * i.qty;
  }, 0);

  const [method, setMethod] = useState<PaymentMethod>("naverpay");
  const [name, setName] = useState("");
  const [customsCode, setCustomsCode] = useState("P");
  const [phoneTail, setPhoneTail] = useState("");
  const [email, setEmail] = useState("");
  const [zonecode, setZonecode] = useState("");
  const [addressBase, setAddressBase] = useState("");
  const [addressDetail, setAddressDetail] = useState("");
  const [profileLoaded, setProfileLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCouponId, setSelectedCouponId] = useState<string>("");

  const orderId = useMemo(
    () => `BRIQ-${Date.now().toString(36).toUpperCase()}`,
    [],
  );

  const phone = `010-${phoneTail}`;
  const canPay =
    name.trim().length > 0 &&
    PHONE_RE.test(`010-${formatPhoneTail(phoneTail)}`) &&
    isValidCustomsCode(customsCode);

  const availableCoupons = useMemo(() => {
    const key = email.trim().toLowerCase() || user?.email?.toLowerCase() || "";
    return coupons
      .filter((c) => c.status === "available")
      .filter((c) => {
        if (user?.id && c.userId === user.id) return true;
        if (key && c.ownerEmail === key) return true;
        return false;
      })
      .sort((a, b) => b.amountKrw - a.amountKrw);
  }, [coupons, email, user?.email, user?.id]);

  const selectedCoupon =
    availableCoupons.find((c) => c.id === selectedCouponId) ?? null;
  const discount = selectedCoupon
    ? Math.min(selectedCoupon.amountKrw, subtotal)
    : 0;
  const total = Math.max(0, subtotal - discount);

  useEffect(() => {
    if (!selectedCouponId && availableCoupons[0]) {
      setSelectedCouponId(availableCoupons[0].id);
    }
    if (
      selectedCouponId &&
      !availableCoupons.some((c) => c.id === selectedCouponId)
    ) {
      setSelectedCouponId(availableCoupons[0]?.id ?? "");
    }
  }, [availableCoupons, selectedCouponId]);

  useEffect(() => {
    loadDaumPostcode().catch(() => {
      /* opened on demand; surface error then */
    });
  }, []);

  useEffect(() => {
    const saved = user?.profile ?? loadCheckoutProfile();
    if (!saved) {
      if (user) {
        setName(user.name);
        if (user.phone?.startsWith("010-")) {
          setPhoneTail(formatPhoneTail(user.phone.slice(4)));
        }
        setEmail(user.email);
      }
      setProfileLoaded(true);
      return;
    }
    setName(saved.name);
    setCustomsCode(saved.customsCode);
    if (saved.phone.startsWith("010-")) {
      setPhoneTail(formatPhoneTail(saved.phone.slice(4)));
    }
    if (saved.email) setEmail(saved.email);
    else if (user?.email) setEmail(user.email);
    setZonecode(saved.zonecode);
    setAddressBase(saved.addressBase);
    setAddressDetail(saved.addressDetail);
    setProfileLoaded(true);
  }, [user]);

  async function openAddressSearch() {
    try {
      await loadDaumPostcode();
    } catch {
      setError("주소 검색을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.");
      return;
    }

    if (!window.daum?.Postcode) {
      setError("주소 검색을 사용할 수 없습니다.");
      return;
    }

    new window.daum.Postcode({
      oncomplete(data) {
        const road = data.roadAddress || data.address;
        const jibun = data.jibunAddress;
        const selected =
          data.userSelectedType === "R" ? road || jibun : jibun || road;

        let extra = "";
        if (data.buildingName) {
          extra =
            data.apartment === "Y"
              ? ` (${data.bname}, ${data.buildingName})`
              : ` (${data.buildingName})`;
        } else if (data.bname) {
          extra = ` (${data.bname})`;
        }

        setZonecode(data.zonecode);
        setAddressBase(`${selected}${extra}`);
        setError(null);
        window.setTimeout(() => detailRef.current?.focus(), 0);
      },
    }).open();
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const fd = new FormData(e.currentTarget);
    const customerName = name.trim();
    const code = normalizeCustomsCode(customsCode);
    const fullPhone = `010-${formatPhoneTail(phoneTail)}`;
    const emailRaw = email.trim() || String(fd.get("email") || "").trim();

    if (!customerName) {
      setBusy(false);
      setError("수취인명을 입력해 주세요.");
      return;
    }

    if (!phoneTail || !PHONE_RE.test(fullPhone)) {
      setBusy(false);
      setError("휴대폰 번호를 010-0000-0000 형식으로 입력해 주세요.");
      return;
    }

    if (!isValidCustomsCode(code)) {
      setBusy(false);
      setError(
        "개인통관부호는 P로 시작하는 13자리(예: P123456789012)로 입력해 주세요.",
      );
      return;
    }

    if (!zonecode || !addressBase.trim()) {
      setBusy(false);
      setError("주소 검색으로 배송지를 선택해 주세요.");
      return;
    }

    if (!addressDetail.trim()) {
      setBusy(false);
      setError("상세 주소(동·호수 등)를 입력해 주세요.");
      return;
    }

    const address = `[${zonecode}] ${addressBase} ${addressDetail.trim()}`;

    const result = await requestPayment({
      orderId,
      amount: total,
      method,
      customerName,
      customerPhone: fullPhone,
      customerEmail: emailRaw || undefined,
      address,
      customsCode: code,
    });

    if (!result.ok) {
      setBusy(false);
      setError(result.message);
      return;
    }

    if (selectedCoupon) {
      markCouponUsed(selectedCoupon.id, orderId);
    }

    // Remember PCCC + shipping for the next checkout on this device
    const profile = {
      name: customerName,
      phone: fullPhone,
      email: emailRaw || undefined,
      customsCode: code,
      zonecode,
      addressBase,
      addressDetail: addressDetail.trim(),
    };
    saveCheckoutProfile(profile);
    if (user) {
      updateProfile({ ...profile, updatedAt: new Date().toISOString() });
      addOrder({
        id: orderId,
        userId: user.id,
        paymentId: result.paymentId,
        status: "paid",
        customsCode: code,
        customerName,
        customerPhone: fullPhone,
        address,
        totalKrw: total,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        paymentMethod:
          paymentMethods.find((m) => m.id === method)?.label ?? method,
        lines: items.map((i) => ({
          productId: i.product.id,
          variantId: i.variant?.id,
          nameKo: i.variant
            ? `${i.product.nameKo} · ${i.variant.nameKo}`
            : i.product.nameKo,
          qty: i.qty,
          unitPrice: i.variant?.price ?? i.product.price,
          image: i.variant?.image ?? i.product.image,
        })),
      });
    }

    recordPurchase(items.map((i) => ({ id: i.product.id, qty: i.qty })));

    // Best-effort support email — works once RESEND_API_KEY is configured
    const paymentLabel =
      paymentMethods.find((m) => m.id === method)?.label ?? method;
    void fetch("/api/notify/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        orderId,
        paymentId: result.paymentId,
        paymentMethod: paymentLabel,
        customerName,
        customerPhone: fullPhone,
        customerEmail: emailRaw || undefined,
        address,
        customsCode: code,
        totalKrw: total,
        lines: items.map((i) => ({
          nameKo: i.variant
            ? `${i.product.nameKo} · ${i.variant.nameKo}`
            : i.product.nameKo,
          qty: i.qty,
          unitPrice: i.variant?.price ?? i.product.price,
        })),
      }),
    }).catch(() => {
      /* never block checkout on mail failure */
    });

    await clearCart();
    router.push(
      `/order/complete?orderId=${encodeURIComponent(orderId)}&paymentId=${encodeURIComponent(result.paymentId)}&msg=${encodeURIComponent(result.message)}`,
    );
  }

  return (
    <section className="section">
      <div className="section__head">
        <div>
          <h2>Checkout</h2>
          <p>주문번호 {orderId}</p>
        </div>
      </div>

      <form className="panel checkout-form" onSubmit={onSubmit}>
        <div className="notice">
          결제사 미계약 상태입니다. 지금은 데모 결제로 주문 흐름만 확인합니다.
          이후 (주)리치몬드인터내셔널 PG 키를 `.env`에 넣으면 네이버페이·카카오페이를
          연결할 수 있게 자리만 마련해 두었습니다.
        </div>

        <div className="field">
          <label htmlFor="name">이름 (수취인명)</label>
          <input
            id="name"
            name="name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="홍길동"
            autoComplete="name"
          />
        </div>

        <div className="field">
          <label htmlFor="phoneTail">휴대폰</label>
          <div className="phone-field">
            <span className="phone-field__prefix" aria-hidden>
              {"010-"}
            </span>
            <input
              id="phoneTail"
              name="phoneTail"
              required
              value={phoneTail}
              onChange={(e) => setPhoneTail(formatPhoneTail(e.target.value))}
              placeholder="1234-5678"
              inputMode="numeric"
              autoComplete="tel-national"
              maxLength={9}
              aria-describedby="phone-hint"
            />
          </div>
          <input type="hidden" name="phone" value={phone} />
          <p id="phone-hint" className="field__hint">
            숫자만 입력해주세요
          </p>
        </div>

        <div className="field">
          <label htmlFor="email">이메일 (선택사항)</label>
          <input
            id="email"
            name="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@email.com"
            autoComplete="email"
          />
        </div>

        <div className="field">
          <label htmlFor="addressBase">배송지</label>
          <div className="address-search">
            <input
              id="zonecode"
              name="zonecode"
              value={zonecode}
              readOnly
              placeholder="우편번호"
              className="address-search__zip"
              onClick={openAddressSearch}
            />
            <button
              type="button"
              className="btn btn-outline address-search__btn"
              onClick={openAddressSearch}
            >
              주소 검색
            </button>
          </div>
          <input
            id="addressBase"
            name="addressBase"
            value={addressBase}
            readOnly
            required
            placeholder="주소 검색을 눌러 도로명/지번을 선택하세요"
            className="address-search__base"
            onClick={openAddressSearch}
          />
          <input
            ref={detailRef}
            id="addressDetail"
            name="addressDetail"
            value={addressDetail}
            onChange={(e) => setAddressDetail(e.target.value)}
            required
            placeholder="상세 주소 (동·호수·건물명 등)"
            autoComplete="address-line2"
          />
          <p className="field__hint">
            카카오(다음) 우편번호 검색 — CJ대한통운 등 택배사가 사용하는 도로명주소
            DB와 동일합니다. 동·건물명 키워드로 검색해 자동 완성하세요.
          </p>
        </div>

        <div className="field">
          <label htmlFor="customsCode">개인통관부호</label>
          <input
            id="customsCode"
            name="customsCode"
            required
            value={customsCode}
            onChange={(e) =>
              setCustomsCode(normalizeCustomsCode(e.target.value).slice(0, 13))
            }
            placeholder="P123456789012"
            autoComplete="off"
            inputMode="text"
            pattern="P[0-9]{12}"
            title="P로 시작하는 13자리 개인통관부호"
            maxLength={13}
            spellCheck={false}
          />
          <p className="field__hint">
            P로 시작하는 개인통관고유부호 13자리를 입력해 주세요. (예: P123456789012)
            {profileLoaded && isValidCustomsCode(customsCode)
              ? " · 이전 결제 정보가 자동으로 불러와졌습니다."
              : " · 결제 완료 후 이 기기에 안전하게 저장되어 다음부터 자동 입력됩니다."}
          </p>
          <div className="customs-alert" role="note">
            <p className="customs-alert__title">[필독] 통관 정보 일치 안내</p>
            <p>
              관세청 정책에 따라 수령인 성명, 전화번호, 개인통관고유부호의 명이 모두
              동일해야 정상 통관이 가능합니다.
            </p>
            <p>
              정보가 불일치할 경우 통관 지연 및 추가 비용이 발생할 수 있으니, 명의가
              일치하는지 반드시 확인해 주세요.
            </p>
          </div>
        </div>

        <div>
          <p style={{ margin: "0 0 0.65rem", fontWeight: 600 }}>결제 수단</p>
          <div className="pay-methods">
            {paymentMethods.map((m) => (
              <button
                key={m.id}
                type="button"
                className={`pay-method ${method === m.id ? "is-active" : ""}`}
                onClick={() => setMethod(m.id)}
              >
                <span>{m.label}</span>
                <small>{m.hint}</small>
              </button>
            ))}
          </div>
        </div>

        <div className="checkout-coupon">
          <p className="checkout-coupon__title">리뷰 쿠폰</p>
          {availableCoupons.length === 0 ? (
            <p className="checkout-coupon__empty">
              사용 가능한 쿠폰이 없습니다. 리뷰 작성 시 텍스트 {formatKrw(3000)} /
              포토·영상 {formatKrw(5000)} 쿠폰이 자동 지급됩니다.
            </p>
          ) : (
            <div className="checkout-coupon__list">
              <label className="checkout-coupon__option">
                <input
                  type="radio"
                  name="coupon"
                  checked={!selectedCouponId}
                  onChange={() => setSelectedCouponId("")}
                />
                <span>쿠폰 사용 안 함</span>
              </label>
              {availableCoupons.map((c) => (
                <label key={c.id} className="checkout-coupon__option">
                  <input
                    type="radio"
                    name="coupon"
                    checked={selectedCouponId === c.id}
                    onChange={() => setSelectedCouponId(c.id)}
                  />
                  <span>
                    <strong>{formatKrw(c.amountKrw)}</strong> · {c.label}
                    <small>{c.productName}</small>
                  </span>
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="checkout-totals">
          <div className="checkout-totals__row">
            <span>상품 합계</span>
            <span>{formatKrw(subtotal)}</span>
          </div>
          {discount > 0 ? (
            <div className="checkout-totals__row checkout-totals__row--discount">
              <span>쿠폰 할인</span>
              <span>-{formatKrw(discount)}</span>
            </div>
          ) : null}
          <div className="checkout-totals__row checkout-totals__row--pay">
            <strong>결제 금액</strong>
            <strong>{formatKrw(total)}</strong>
          </div>
          <button type="submit" className="btn btn-solid" disabled={busy || !canPay}>
            {busy ? "처리 중…" : "결제하기"}
          </button>
        </div>

        {error ? <p style={{ color: "var(--danger)", margin: 0 }}>{error}</p> : null}
      </form>
    </section>
  );
}
