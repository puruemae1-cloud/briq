"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { AccountNav } from "@/components/AccountNav";
import {
  isValidCustomsCode,
  normalizeCustomsCode,
  saveCheckoutProfile,
  type CheckoutProfile,
} from "@/lib/checkout-profile";
import { useAuthStore } from "@/lib/auth-store";

export function AccountProfile() {
  const user = useAuthStore((s) => s.currentUser());
  const updateProfile = useAuthStore((s) => s.updateProfile);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [customsCode, setCustomsCode] = useState("P");
  const [zonecode, setZonecode] = useState("");
  const [addressBase, setAddressBase] = useState("");
  const [addressDetail, setAddressDetail] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    const p = user.profile;
    setName(p?.name || user.name);
    setPhone(p?.phone || user.phone || "");
    setCustomsCode(p?.customsCode || "P");
    setZonecode(p?.zonecode || "");
    setAddressBase(p?.addressBase || "");
    setAddressDetail(p?.addressDetail || "");
  }, [user]);

  if (!user) {
    return (
      <section className="section">
        <div className="panel account-gate">
          <h1>통관·배송정보</h1>
          <p>로그인 후 저장할 수 있습니다.</p>
          <Link href="/account/login?next=/account/profile" className="btn btn-solid">
            로그인
          </Link>
        </div>
      </section>
    );
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const code = normalizeCustomsCode(customsCode);
    if (!isValidCustomsCode(code)) {
      setError("개인통관부호는 P + 숫자 12자리여야 합니다.");
      return;
    }
    if (!name.trim() || !phone.trim()) {
      setError("이름과 휴대폰을 입력해 주세요.");
      return;
    }

    const profile: CheckoutProfile = {
      name: name.trim(),
      phone: phone.trim(),
      email: user!.email,
      customsCode: code,
      zonecode: zonecode.trim(),
      addressBase: addressBase.trim(),
      addressDetail: addressDetail.trim(),
      updatedAt: new Date().toISOString(),
    };

    updateProfile(profile);
    saveCheckoutProfile(profile);
    setError(null);
    setSaved(true);
  }

  return (
    <section className="section account-shell">
      <div className="account-layout">
        <AccountNav />
        <div className="account-main">
          <header className="account-main__head">
            <p className="product-card__brand">Profile</p>
            <h1>통관·배송정보</h1>
            <p>한 번 저장하면 다음 결제부터 자동으로 불러옵니다.</p>
          </header>

          <form className="panel account-form" onSubmit={onSubmit}>
            <div className="field">
              <label htmlFor="profile-name">수취인명</label>
              <input
                id="profile-name"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="profile-phone">휴대폰</label>
              <input
                id="profile-phone"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="010-0000-0000"
              />
            </div>
            <div className="field">
              <label htmlFor="profile-customs">개인통관부호</label>
              <input
                id="profile-customs"
                required
                value={customsCode}
                onChange={(e) =>
                  setCustomsCode(normalizeCustomsCode(e.target.value).slice(0, 13))
                }
                maxLength={13}
                placeholder="P123456789012"
              />
            </div>
            <div className="field">
              <label htmlFor="profile-zip">우편번호</label>
              <input
                id="profile-zip"
                value={zonecode}
                onChange={(e) => setZonecode(e.target.value)}
                placeholder="06236"
              />
            </div>
            <div className="field">
              <label htmlFor="profile-addr">주소</label>
              <input
                id="profile-addr"
                value={addressBase}
                onChange={(e) => setAddressBase(e.target.value)}
                placeholder="도로명 주소"
              />
            </div>
            <div className="field">
              <label htmlFor="profile-detail">상세 주소</label>
              <input
                id="profile-detail"
                value={addressDetail}
                onChange={(e) => setAddressDetail(e.target.value)}
                placeholder="동·호수"
              />
            </div>

            {error ? <p className="account-form__error">{error}</p> : null}
            {saved ? (
              <p className="account-form__ok">저장되었습니다. 다음 결제에 자동 반영됩니다.</p>
            ) : null}

            <button type="submit" className="btn btn-solid">
              저장하기
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
