"use client";

import React, { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { 
  ChevronLeft, Building2, Settings2, SlidersHorizontal, 
  Globe, Download, Shield, LogOut, KeyRound, Camera
} from 'lucide-react';
import AnimatedButton from '@/components/AnimatedButton';
import { useLanguage } from '@/context/LanguageContext';

const SectionCard = ({ icon: Icon, title, children }) => {
  const { t } = useLanguage();
  return (
    <div className="bg-white border border-[#EBEBEB] rounded-lg mb-8 overflow-hidden">
      <div className="px-4 py-3 border-b border-[#EBEBEB] bg-[#FAFAFA] flex items-center gap-2">
        <Icon size={16} className="text-[#111111]" />
        <h2 className="text-xs font-extrabold uppercase tracking-wider text-[#111111]">{t(title)}</h2>
      </div>
      <div className="p-4 flex flex-col gap-4">
        {children}
      </div>
    </div>
  );
};

const AvatarUpload = ({ fileInputRef, handleFileChange, handleAvatarClick, isUploading, profilePicUrl, businessName }) => (
  <>
    <input
      ref={fileInputRef}
      type="file"
      accept="image/jpeg,image/png,image/webp,image/gif"
      className="hidden"
      onChange={handleFileChange}
      id="avatar-file-input"
    />
    <button
      type="button"
      onClick={handleAvatarClick}
      disabled={isUploading}
      className="relative w-16 h-16 rounded-full shrink-0 group focus:outline-none focus:ring-2 focus:ring-[#111111] focus:ring-offset-2 transition-all"
      aria-label="Upload profile picture"
      id="avatar-upload-btn"
    >
      {isUploading && (
        <div className="absolute inset-0 rounded-full overflow-hidden">
          <div
            className="w-full h-full rounded-full bg-gradient-to-r from-[#E0E0E0] via-[#F5F5F5] to-[#E0E0E0]"
            style={{
              backgroundSize: '200% 100%',
              animation: 'skeletonPulse 1.4s ease-in-out infinite',
            }}
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <svg className="w-6 h-6 text-[#888888]" style={{ animation: 'spin 1s linear infinite' }} viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="50 100" />
            </svg>
          </div>
        </div>
      )}

      {!isUploading && profilePicUrl && (
        <img
          src={profilePicUrl}
          alt="Profile"
          className="w-full h-full rounded-full object-cover"
        />
      )}

      {!isUploading && !profilePicUrl && (
        <div className="w-full h-full rounded-full bg-[#111111] flex items-center justify-center text-white text-xl font-black">
          {(businessName || "JS").substring(0, 2).toUpperCase()}
        </div>
      )}

      {!isUploading && (
        <div className="absolute inset-0 rounded-full bg-black/0 group-hover:bg-black/40 flex items-center justify-center transition-all duration-200">
          <Camera
            size={18}
            className="text-white opacity-0 group-hover:opacity-100 transition-opacity duration-200"
          />
        </div>
      )}
    </button>
    <style jsx>{`
      @keyframes skeletonPulse {
        0%   { background-position: 200% 0; }
        100% { background-position: -200% 0; }
      }
      @keyframes spin {
        from { transform: rotate(0deg); }
        to   { transform: rotate(360deg); }
      }
    `}</style>
  </>
);

export default function ProfileSettings() {
  const router = useRouter();

  const getApiBase = () => {
    let API_BASE = process.env.NEXT_PUBLIC_API_URL;
    if (!API_BASE) {
      if (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
        API_BASE = "https://go-chicken.vercel.app/api/v1";
      } else {
        API_BASE = "http://localhost:8000/api/v1";
      }
    }
    API_BASE = API_BASE.replace(/\/+$/, "");
    if (!API_BASE.endsWith("/api/v1")) API_BASE += "/api/v1";
    return API_BASE;
  };

  // Local state for the settings
  const [basePrice, setBasePrice] = useState(135);
  const [creditLimit, setCreditLimit] = useState(100000);
  const [iotAlerts, setIotAlerts] = useState(true);
  const [khataAlerts, setKhataAlerts] = useState(true);
  const { language: globalLanguage, setLanguage: setGlobalLanguage, t } = useLanguage();
  const [language, setLanguage] = useState('English');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Profile details state
  const [businessName, setBusinessName] = useState('Jagan Supplies');
  const [role, setRole] = useState('Super Admin');
  const [adminName, setAdminName] = useState('Jagan Mohan');
  const [contactNumber, setContactNumber] = useState('+91 98765 43210');
  const [gstin, setGstin] = useState('37AAACJ1234A1Z5');
  const [hubLocation, setHubLocation] = useState('Vijayawada Hub');

  // Avatar upload state
  const [profilePicUrl, setProfilePicUrl] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);

  React.useEffect(() => {
    async function fetchProfile() {
      const token = localStorage.getItem('gc_user');
      if (!token) {
        router.replace('/landing');
        return;
      }
      try {
        const res = await fetch(`${getApiBase()}/profile`, {
          credentials: "include"
        });
        if (res.ok) {
          const data = await res.json();
          if (data.base_price_today !== null) setBasePrice(Number(data.base_price_today));
          if (data.default_credit_limit !== null) setCreditLimit(Number(data.default_credit_limit));
          if (data.iot_alerts_enabled !== null) setIotAlerts(data.iot_alerts_enabled);
          if (data.financial_alerts_enabled !== null) setKhataAlerts(data.financial_alerts_enabled);
          if (data.app_language !== null) {
            setLanguage(data.app_language);
            setGlobalLanguage(data.app_language);
          }
          if (data.business_name !== null) setBusinessName(data.business_name);
          if (data.role !== null) setRole(data.role);
          if (data.admin_name !== null) setAdminName(data.admin_name);
          if (data.contact_number !== null) setContactNumber(data.contact_number);
          if (data.gstin !== null) setGstin(data.gstin);
          if (data.hub_location !== null) setHubLocation(data.hub_location);
          if (data.profile_pic_url) setProfilePicUrl(data.profile_pic_url);
        }
      } catch (err) {
        console.error('Failed to fetch profile', err);
      } finally {
        setIsLoading(false);
      }
    }
    fetchProfile();
  }, []);

  const handleAvatarClick = () => {
    if (!isUploading) {
      fileInputRef.current?.click();
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate client-side before uploading
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
      alert('Please select a valid image file (JPEG, PNG, WebP, or GIF).');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      alert('Image must be under 5 MB.');
      return;
    }

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const token = localStorage.getItem('gc_user');
      const res = await fetch(`${getApiBase()}/profile/upload_avatar`, {
        method: 'POST',
        credentials: "include",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Upload failed');
      }

      const data = await res.json();
      if (data.profile_pic_url) {
        setProfilePicUrl(data.profile_pic_url);
      }
    } catch (err) {
      console.error('Avatar upload error:', err);
      alert(err.message || 'Failed to upload profile picture.');
    } finally {
      setIsUploading(false);
      // Reset the input so the same file can be re-selected
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const payload = {
        base_price_today: basePrice,
        default_credit_limit: creditLimit,
        iot_alerts_enabled: iotAlerts,
        financial_alerts_enabled: khataAlerts,
        app_language: language,
        business_name: businessName,
        role: role,
        admin_name: adminName,
        contact_number: contactNumber,
        gstin: gstin,
        hub_location: hubLocation,
      };
      const token = localStorage.getItem('gc_user');
      const res = await fetch(`${getApiBase()}/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: "include",
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        throw new Error('Failed to update profile');
      }
      setGlobalLanguage(language);
      alert('Trade Settings Saved Successfully!');
    } catch (err) {
      console.error(err);
      alert('Failed to save settings.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleExportCsv = async () => {
    try {
      const token = localStorage.getItem('gc_user');
      const res = await fetch(`${getApiBase()}/profile/export`, {
        credentials: "include"
      });
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'go_chicken_export.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert('Failed to export CSV.');
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${getApiBase()}/auth/logout`, {
        method: 'POST',
        credentials: "include"
      });
    } catch(err) {
      console.error(err);
    }
    localStorage.removeItem('gc_user');
    sessionStorage.clear();
    router.replace('/login');
  };



  return (
    <div
      className="min-h-screen text-[#111111] font-sans pb-12"
      style={{
        backgroundColor: '#FAFAFA',
        backgroundImage: "url('/chicken-pattern.svg')",
        backgroundRepeat: 'repeat',
        backgroundSize: '500px 500px',
      }}
    >
      {/* ── Top App Bar ── */}
      <header className="sticky top-0 z-50 bg-white border-b border-[#EBEBEB] px-4 py-3 flex items-center gap-3">
        <button 
          onClick={() => router.back()}
          className="p-1.5 -ml-1.5 hover:bg-[#FAFAFA] rounded-md transition-colors"
        >
          <ChevronLeft size={24} className="text-[#111111]" />
        </button>
        <h1 className="text-sm font-extrabold tracking-tight uppercase">{t('Profile & Settings')}</h1>
      </header>

      <main className="max-w-3xl mx-auto p-4 mt-2">
        
        {/* ── 1. Business Profile ── */}
        <SectionCard icon={Building2} title="Business Profile">
          <div className="flex items-center gap-4 mb-4">
            <AvatarUpload
              fileInputRef={fileInputRef}
              handleFileChange={handleFileChange}
              handleAvatarClick={handleAvatarClick}
              isUploading={isUploading}
              profilePicUrl={profilePicUrl}
              businessName={businessName}
            />
            <div className="flex-1">
              <input type="text" value={businessName} onChange={(e) => setBusinessName(e.target.value)} className="text-lg font-bold bg-transparent border-b border-transparent hover:border-[#EBEBEB] focus:border-[#111111] focus:outline-none transition-colors px-1 -ml-1 w-full max-w-xs" />
              <input type="text" value={role} onChange={(e) => setRole(e.target.value)} className="text-[#666666] block text-xs font-bold uppercase tracking-wider mt-0.5 bg-transparent border-b border-transparent hover:border-[#EBEBEB] focus:border-[#111111] focus:outline-none transition-colors px-1 -ml-1 w-full max-w-xs" />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
            <div>
              <label className="block text-sm font-semibold capitalize tracking-wide text-[#666666] mb-1">{t('Admin Name')}</label>
              <input type="text" value={adminName} onChange={(e) => setAdminName(e.target.value)} className="w-full px-3 py-2 bg-white border border-[#EBEBEB] rounded-md text-sm font-semibold text-[#111111] focus:outline-none focus:border-[#111111] transition-colors" />
            </div>
            <div>
              <label className="block text-sm font-semibold capitalize tracking-wide text-[#666666] mb-1">{t('Contact Number')}</label>
              <input type="text" value={contactNumber} onChange={(e) => setContactNumber(e.target.value)} className="w-full px-3 py-2 bg-white border border-[#EBEBEB] rounded-md text-sm font-semibold text-[#111111] focus:outline-none focus:border-[#111111] transition-colors" />
            </div>
            <div>
              <label className="block text-sm font-semibold capitalize tracking-wide text-[#666666] mb-1">{t('GSTIN')}</label>
              <input type="text" value={gstin} onChange={(e) => setGstin(e.target.value)} className="w-full px-3 py-2 bg-white border border-[#EBEBEB] rounded-md text-sm font-semibold text-[#111111] focus:outline-none focus:border-[#111111] transition-colors" />
            </div>
            <div>
              <label className="block text-sm font-semibold capitalize tracking-wide text-[#666666] mb-1">{t('Hub Location')}</label>
              <input type="text" value={hubLocation} onChange={(e) => setHubLocation(e.target.value)} className="w-full px-3 py-2 bg-white border border-[#EBEBEB] rounded-md text-sm font-semibold text-[#111111] focus:outline-none focus:border-[#111111] transition-colors" />
            </div>
          </div>
        </SectionCard>

        {/* ── 2. Trade Settings ── */}
        <SectionCard icon={Settings2} title="Operational & Trade Settings">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold capitalize tracking-wide text-[#111111] mb-1">{t("Today's Base Price (₹/kg)")}</label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-[#666666] font-bold text-sm">₹</span>
                <input 
                  type="number" 
                  value={basePrice} 
                  onChange={(e) => setBasePrice(e.target.value)}
                  className="w-full pl-8 pr-3 py-2 bg-white border border-[#EBEBEB] rounded-md text-sm font-bold text-[#111111] focus:outline-none focus:border-[#111111] transition-colors" 
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold capitalize tracking-wide text-[#111111] mb-1">{t('Default Credit Limit (₹)')}</label>
              <div className="relative">
                <span className="absolute left-3 top-2.5 text-[#666666] font-bold text-sm">₹</span>
                <input 
                  type="number" 
                  value={creditLimit}
                  onChange={(e) => setCreditLimit(e.target.value)}
                  className="w-full pl-8 pr-3 py-2 bg-white border border-[#EBEBEB] rounded-md text-sm font-bold text-[#111111] focus:outline-none focus:border-[#111111] transition-colors" 
                />
              </div>
            </div>
          </div>
        </SectionCard>

        {/* ── 3. Preferences ── */}
        <SectionCard icon={SlidersHorizontal} title="Notification & IoT Preferences">
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="text-sm font-bold text-[#111111]">{t('IoT Fleet Alerts')}</p>
              <p className="text-xs text-[#666666] mt-0.5">{t('Notify when truck temp > 30°C')}</p>
            </div>
            <button 
              onClick={() => setIotAlerts(!iotAlerts)}
              className={`w-11 h-6 rounded-full border transition-colors flex items-center px-0.5 ${iotAlerts ? 'bg-[#111111] border-[#111111]' : 'bg-[#FAFAFA] border-[#EBEBEB]'}`}
            >
              <div className={`w-4 h-4 rounded-full bg-white transition-transform ${iotAlerts ? 'translate-x-5' : 'translate-x-0 border border-[#EBEBEB]'}`}></div>
            </button>
          </div>
          <div className="w-full h-px bg-[#EBEBEB]"></div>
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="text-sm font-bold text-[#111111]">{t('Financial Alerts')}</p>
              <p className="text-xs text-[#666666] mt-0.5">{t('Daily settlement and overdue Khata notices')}</p>
            </div>
            <button 
              onClick={() => setKhataAlerts(!khataAlerts)}
              className={`w-11 h-6 rounded-full border transition-colors flex items-center px-0.5 ${khataAlerts ? 'bg-[#111111] border-[#111111]' : 'bg-[#FAFAFA] border-[#EBEBEB]'}`}
            >
              <div className={`w-4 h-4 rounded-full bg-white transition-transform ${khataAlerts ? 'translate-x-5' : 'translate-x-0 border border-[#EBEBEB]'}`}></div>
            </button>
          </div>
        </SectionCard>

        {/* ── 4. System ── */}
        <SectionCard icon={Globe} title="System">
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="text-sm font-bold text-[#111111]">{t('App Language')}</p>
              <p className="text-xs text-[#666666] mt-0.5">{t('Local staff preference')}</p>
            </div>
            <div className="flex bg-[#FAFAFA] border border-[#EBEBEB] rounded-lg p-1">
              <button 
                onClick={() => setLanguage('English')}
                className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${language === 'English' ? 'bg-white shadow-sm border border-[#EBEBEB] text-[#111111]' : 'text-[#666666]'}`}
              >
                ENG
              </button>
              <button 
                onClick={() => setLanguage('Telugu')}
                className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${language === 'Telugu' ? 'bg-white shadow-sm border border-[#EBEBEB] text-[#111111]' : 'text-[#666666]'}`}
              >
                తెలుగు
              </button>
            </div>
          </div>
          <div className="w-full h-px bg-[#EBEBEB]"></div>
          <div className="py-2 flex justify-between items-center">
            <div>
              <p className="text-sm font-bold text-[#111111]">{t('Data Export')}</p>
              <p className="text-xs text-[#666666] mt-0.5">{t('Monthly Khata and Order reports')}</p>
            </div>
            <button 
              onClick={handleExportCsv}
              className="flex items-center gap-2 px-4 py-2 border border-[#EBEBEB] hover:border-[#111111] hover:bg-[#FAFAFA] text-[#111111] text-xs font-bold uppercase tracking-wider rounded-md transition-all">
              <Download size={14} /> {t('Export CSV')}
            </button>
          </div>
        </SectionCard>

        {/* ── 5. Security (Danger Zone) ── */}
        <SectionCard icon={Shield} title="Security">
          <div className="flex flex-col gap-3">
            <button className="w-full flex items-center justify-center gap-2 px-4 py-3 border border-[#EBEBEB] hover:border-[#111111] hover:bg-[#FAFAFA] text-[#111111] text-xs font-bold uppercase tracking-wider rounded-md transition-all">
              <KeyRound size={16} /> {t('Reset Admin Password')}
            </button>
            <button onClick={handleLogout} className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-[#111111] hover:bg-black text-white text-xs font-bold uppercase tracking-wider rounded-md transition-all">
              <LogOut size={16} /> {t('Log Out from Go Chicken')}
            </button>
          </div>
        </SectionCard>

      </main>

      {/* ── Fixed Bottom Action Bar ── */}
      <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-[#EBEBEB] shadow-[0_-4px_20px_rgb(0,0,0,0.05)] z-50">
        <div className="max-w-3xl mx-auto flex justify-end">
          <AnimatedButton className="w-full md:w-[280px]" onClick={handleSave} disabled={isSaving || isLoading}>
            {isSaving ? t('Saving...') : t('Save Trade Settings')}
          </AnimatedButton>
        </div>
      </div>
    </div>
  );
}
