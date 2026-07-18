"use client"

import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { 
  ChevronLeft, Building2, Settings2, SlidersHorizontal, 
  Globe, Download, Shield, LogOut, KeyRound, Camera
} from 'lucide-react';
import AnimatedButton from '@/components/AnimatedButton';
import { useLanguage } from '@/context/LanguageContext';
import { useUI } from '@/context/UIContext';

// ── UTILITIES ──

const getApiBase = () => {
  let API_BASE = process.env.NEXT_PUBLIC_API_URL;
  if (!API_BASE) {
    if (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
      API_BASE = "https://go-chicken-production.up.railway.app/api/v1";
    } else {
      API_BASE = "http://localhost:8000/api/v1";
    }
  }
  API_BASE = API_BASE.replace(/\/+$/, "");
  if (!API_BASE.endsWith("/api/v1")) API_BASE += "/api/v1";
  return API_BASE;
};

// Normalize form state for comparison
const normalizeForm = (data) => {
  if (!data) return null;
  return {
    base_price_today: data.base_price_today === null || data.base_price_today === '' ? '' : Number(data.base_price_today),
    default_credit_limit: data.default_credit_limit === null || data.default_credit_limit === '' ? '' : Number(data.default_credit_limit),
    iot_alerts_enabled: !!data.iot_alerts_enabled,
    financial_alerts_enabled: !!data.financial_alerts_enabled,
    app_language: (data.app_language || 'English').trim(),
    business_name: (data.business_name || '').trim(),
    role: (data.role || '').trim(),
    admin_name: (data.admin_name || '').trim(),
    contact_number: (data.contact_number || '').trim(),
    gstin: (data.gstin || '').trim(),
    hub_location: (data.hub_location || '').trim(),
  };
};

const isDeepEqual = (obj1, obj2) => {
  if (!obj1 || !obj2) return obj1 === obj2;
  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);
  if (keys1.length !== keys2.length) return false;
  for (let key of keys1) {
    if (obj1[key] !== obj2[key]) return false;
  }
  return true;
};

// ── COMPONENTS ──

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

const ProfileSkeleton = () => (
  <div className="animate-pulse flex flex-col gap-8 mt-2 max-w-3xl mx-auto p-4">
    {[1, 2, 3].map(i => (
      <div key={i} className="bg-white border border-[#EBEBEB] rounded-lg overflow-hidden">
        <div className="h-10 bg-[#FAFAFA] border-b border-[#EBEBEB]"></div>
        <div className="p-4 flex flex-col gap-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="h-10 bg-gray-100 rounded w-full"></div>
          <div className="h-10 bg-gray-100 rounded w-full"></div>
        </div>
      </div>
    ))}
  </div>
);

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
  const { language: globalLanguage, setLanguage: setGlobalLanguage, t } = useLanguage();
  const { addToast } = useUI();

  // ── STATE MACHINES ──
  // Page Lifecycle: 'loading' | 'ready' | 'unauthorized' | 'fatal_error'
  const [pageState, setPageState] = useState('loading');
  
  // Save Lifecycle: 'idle' | 'saving' | 'saved' | 'save_error'
  // Note: 'dirty' is a derived state.
  const [saveLifecycle, setSaveLifecycle] = useState('idle');

  // ── DATA STATE ──
  const [originalForm, setOriginalForm] = useState(null);
  const [currentForm, setCurrentForm] = useState(null);
  
  // Avatar is separate from the form state because it's an immediate action.
  const [profilePicUrl, setProfilePicUrl] = useState(null);
  const [isAvatarUploading, setIsAvatarUploading] = useState(false);
  const fileInputRef = useRef(null);
  const saveTimeoutRef = useRef(null);

  // ── DERIVED STATE ──
  const isDirty = useMemo(() => {
    if (!originalForm || !currentForm) return false;
    return !isDeepEqual(originalForm, currentForm);
  }, [originalForm, currentForm]);

  // ── FETCH HELPER (Handles 401 globally) ──
  const fetchWithAuth = useCallback(async (url, options = {}) => {
    options.credentials = "include";
    try {
      const response = await fetch(url, options);
      if (response.status === 401) {
        setPageState('unauthorized');
        localStorage.removeItem('gc_user');
        sessionStorage.clear();
        router.replace('/login');
        return { error: 'unauthorized', response: null };
      }
      return { error: null, response };
    } catch (err) {
      return { error: 'network_error', response: null };
    }
  }, [router]);

  // ── LOAD PROFILE ──
  useEffect(() => {
    let isMounted = true;
    async function loadProfile() {
      setPageState('loading');
      
      const { error, response } = await fetchWithAuth(`${getApiBase()}/profile`);
      
      if (!isMounted) return;

      if (error === 'unauthorized') {
        return; // Handled by fetchWithAuth
      }
      if (error || !response.ok) {
        setPageState('fatal_error');
        return;
      }

      try {
        const data = await response.json();
        const normalized = normalizeForm(data);
        setOriginalForm(normalized);
        setCurrentForm(normalized);
        setProfilePicUrl(data.profile_pic_url || null);
        setPageState('ready');
      } catch (err) {
        setPageState('fatal_error');
      }
    }
    loadProfile();
    return () => { 
      isMounted = false;
      if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    };
  }, [fetchWithAuth]);

  // ── UNSAVED CHANGES WARNING ──
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    if (isDirty) {
      window.addEventListener('beforeunload', handleBeforeUnload);
    }
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  // ── HANDLERS ──
  const updateField = (field, value) => {
    setCurrentForm(prev => {
      if (!prev) return prev;
      return { ...prev, [field]: value };
    });
    setSaveLifecycle('idle'); // Reset saved state if they edit again
  };

  const handleAvatarClick = () => {
    if (!isAvatarUploading) {
      fileInputRef.current?.click();
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
      addToast('Please select a valid image file (JPEG, PNG, WebP, GIF).', 'error');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      addToast('Image must be under 5 MB.', 'error');
      return;
    }

    setIsAvatarUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    const { error, response } = await fetchWithAuth(`${getApiBase()}/profile/upload_avatar`, {
      method: 'POST',
      body: formData,
    });

    setIsAvatarUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';

    if (error === 'unauthorized') return;
    
    if (error || !response.ok) {
      addToast('Failed to upload profile picture.', 'error');
    } else {
      const data = await response.json();
      if (data.profile_pic_url) {
        setProfilePicUrl(data.profile_pic_url);
        addToast('Avatar updated successfully!', 'success');
      }
    }
  };

  const handleSave = async () => {
    if (!isDirty) return;
    
    setSaveLifecycle('saving');
    
    // Safety check - construct payload explicitly from currentForm
    const payload = {
      base_price_today: currentForm.base_price_today === '' ? null : currentForm.base_price_today,
      default_credit_limit: currentForm.default_credit_limit === '' ? null : currentForm.default_credit_limit,
      iot_alerts_enabled: currentForm.iot_alerts_enabled,
      financial_alerts_enabled: currentForm.financial_alerts_enabled,
      app_language: currentForm.app_language,
      business_name: currentForm.business_name,
      role: currentForm.role,
      admin_name: currentForm.admin_name,
      contact_number: currentForm.contact_number,
      gstin: currentForm.gstin,
      hub_location: currentForm.hub_location,
    };

    const { error, response } = await fetchWithAuth(`${getApiBase()}/profile`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (error === 'unauthorized') return;

    if (error || !response.ok) {
      setSaveLifecycle('save_error');
      let msg = 'Failed to save settings.';
      try {
        const errData = await response.json();
        if (errData.detail) {
          if (Array.isArray(errData.detail)) {
              msg = errData.detail.map(e => e.msg).join(", ");
          } else {
              msg = errData.detail;
          }
        }
      } catch(e) {}
      addToast(msg, 'error');
    } else {
      const data = await response.json();
      const normalized = normalizeForm(data);
      setOriginalForm(normalized);
      setCurrentForm(normalized);
      setGlobalLanguage(normalized.app_language);
      setSaveLifecycle('saved');
      addToast('Trade Settings Saved Successfully!', 'success');
      
      if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
      saveTimeoutRef.current = setTimeout(() => {
        setSaveLifecycle(prev => prev === 'saved' ? 'idle' : prev);
      }, 3000);
    }
  };

  const handleExportCsv = async () => {
    try {
      const { error, response } = await fetchWithAuth(`${getApiBase()}/profile/export`);
      if (error === 'unauthorized') return;
      if (error || !response.ok) throw new Error('Export failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'go_chicken_export.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      addToast('Export downloaded successfully.', 'success');
    } catch (err) {
      addToast('Failed to export CSV.', 'error');
    }
  };

  const handleLogout = async () => {
    try {
      await fetchWithAuth(`${getApiBase()}/auth/logout`, { method: 'POST' });
    } catch(err) {}
    localStorage.removeItem('gc_user');
    sessionStorage.clear();
    router.replace('/login');
  };

  // ── RENDERERS ──

  if (pageState === 'loading') {
    return (
      <div className="min-h-screen bg-[#FAFAFA]">
        <header className="sticky top-0 z-50 bg-white border-b border-[#EBEBEB] px-4 py-3 flex items-center gap-3">
          <button className="p-1.5 -ml-1.5 hover:bg-[#FAFAFA] rounded-md transition-colors">
            <ChevronLeft size={24} className="text-[#111111]" />
          </button>
          <h1 className="text-sm font-extrabold tracking-tight uppercase">{t('Profile & Settings')}</h1>
        </header>
        <ProfileSkeleton />
      </div>
    );
  }

  if (pageState === 'fatal_error' || pageState === 'unauthorized') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FAFAFA]">
        <div className="text-center">
          <h2 className="text-lg font-bold text-[#111111] mb-2">Unable to load profile</h2>
          <p className="text-[#666666] mb-4">Please check your connection and try again.</p>
          <AnimatedButton onClick={() => window.location.reload()}>Retry</AnimatedButton>
        </div>
      </div>
    );
  }

  return (
    <div
      className="min-h-screen text-[#111111] font-sans pb-24"
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
              isUploading={isAvatarUploading}
              profilePicUrl={profilePicUrl}
              businessName={currentForm?.business_name}
            />
            <div className="flex-1">
              <input 
                type="text" 
                value={currentForm.business_name} 
                onChange={(e) => updateField('business_name', e.target.value)} 
                maxLength={255}
                placeholder="Business Name"
                className="text-lg font-bold bg-transparent border-b border-transparent hover:border-[#EBEBEB] focus:border-[#111111] focus:outline-none transition-colors px-1 -ml-1 w-full max-w-xs" 
              />
              <input 
                type="text" 
                value={currentForm.role} 
                onChange={(e) => updateField('role', e.target.value)} 
                maxLength={100}
                placeholder="Role"
                className="text-[#666666] block text-xs font-bold uppercase tracking-wider mt-0.5 bg-transparent border-b border-transparent hover:border-[#EBEBEB] focus:border-[#111111] focus:outline-none transition-colors px-1 -ml-1 w-full max-w-xs" 
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
            <div>
              <label className="block text-sm font-semibold capitalize tracking-wide text-[#666666] mb-1">{t('Admin Name')}</label>
              <input type="text" maxLength={255} value={currentForm.admin_name} onChange={(e) => updateField('admin_name', e.target.value)} className="w-full px-3 py-2 bg-white border border-[#EBEBEB] rounded-md text-sm font-semibold text-[#111111] focus:outline-none focus:border-[#111111] transition-colors" />
            </div>
            <div>
              <label className="block text-sm font-semibold capitalize tracking-wide text-[#666666] mb-1">{t('Contact Number')}</label>
              <input type="text" maxLength={20} value={currentForm.contact_number} onChange={(e) => updateField('contact_number', e.target.value.replace(/[^0-9+]/g, ''))} className="w-full px-3 py-2 bg-white border border-[#EBEBEB] rounded-md text-sm font-semibold text-[#111111] focus:outline-none focus:border-[#111111] transition-colors" />
            </div>
            <div>
              <label className="block text-sm font-semibold capitalize tracking-wide text-[#666666] mb-1">{t('GSTIN')}</label>
              <input type="text" maxLength={15} value={currentForm.gstin} onChange={(e) => updateField('gstin', e.target.value.toUpperCase())} className="w-full px-3 py-2 bg-white border border-[#EBEBEB] rounded-md text-sm font-semibold text-[#111111] focus:outline-none focus:border-[#111111] transition-colors" />
            </div>
            <div>
              <label className="block text-sm font-semibold capitalize tracking-wide text-[#666666] mb-1">{t('Hub Location')}</label>
              <input type="text" maxLength={255} value={currentForm.hub_location} onChange={(e) => updateField('hub_location', e.target.value)} className="w-full px-3 py-2 bg-white border border-[#EBEBEB] rounded-md text-sm font-semibold text-[#111111] focus:outline-none focus:border-[#111111] transition-colors" />
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
                  min="0"
                  step="0.01"
                  value={currentForm.base_price_today} 
                  onChange={(e) => updateField('base_price_today', e.target.value)}
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
                  min="0"
                  step="0.01"
                  value={currentForm.default_credit_limit}
                  onChange={(e) => updateField('default_credit_limit', e.target.value)}
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
              onClick={() => updateField('iot_alerts_enabled', !currentForm.iot_alerts_enabled)}
              className={`w-11 h-6 rounded-full border transition-colors flex items-center px-0.5 ${currentForm.iot_alerts_enabled ? 'bg-[#111111] border-[#111111]' : 'bg-[#FAFAFA] border-[#EBEBEB]'}`}
            >
              <div className={`w-4 h-4 rounded-full bg-white transition-transform ${currentForm.iot_alerts_enabled ? 'translate-x-5' : 'translate-x-0 border border-[#EBEBEB]'}`}></div>
            </button>
          </div>
          <div className="w-full h-px bg-[#EBEBEB]"></div>
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="text-sm font-bold text-[#111111]">{t('Financial Alerts')}</p>
              <p className="text-xs text-[#666666] mt-0.5">{t('Daily settlement and overdue Khata notices')}</p>
            </div>
            <button 
              onClick={() => updateField('financial_alerts_enabled', !currentForm.financial_alerts_enabled)}
              className={`w-11 h-6 rounded-full border transition-colors flex items-center px-0.5 ${currentForm.financial_alerts_enabled ? 'bg-[#111111] border-[#111111]' : 'bg-[#FAFAFA] border-[#EBEBEB]'}`}
            >
              <div className={`w-4 h-4 rounded-full bg-white transition-transform ${currentForm.financial_alerts_enabled ? 'translate-x-5' : 'translate-x-0 border border-[#EBEBEB]'}`}></div>
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
                onClick={() => updateField('app_language', 'English')}
                className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${currentForm.app_language === 'English' ? 'bg-white shadow-sm border border-[#EBEBEB] text-[#111111]' : 'text-[#666666]'}`}
              >
                ENG
              </button>
              <button 
                onClick={() => updateField('app_language', 'Telugu')}
                className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${currentForm.app_language === 'Telugu' ? 'bg-white shadow-sm border border-[#EBEBEB] text-[#111111]' : 'text-[#666666]'}`}
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
            <button onClick={() => addToast('Password reset email sent (simulation)', 'success')} className="w-full flex items-center justify-center gap-2 px-4 py-3 border border-[#EBEBEB] hover:border-[#111111] hover:bg-[#FAFAFA] text-[#111111] text-xs font-bold uppercase tracking-wider rounded-md transition-all">
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
        <div className="max-w-3xl mx-auto flex justify-end items-center gap-4">
          {isDirty && <span className="text-xs font-bold text-amber-600 hidden md:block">Unsaved changes</span>}
          <AnimatedButton 
            className="w-full md:w-[280px]" 
            onClick={handleSave} 
            disabled={!isDirty || saveLifecycle === 'saving'}
          >
            {saveLifecycle === 'saving' ? t('Saving...') : saveLifecycle === 'saved' ? t('Saved ✓') : t('Save Trade Settings')}
          </AnimatedButton>
        </div>
      </div>
    </div>
  );
}
