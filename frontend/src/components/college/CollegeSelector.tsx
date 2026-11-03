'use client';

import React, { useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api/client';
import { College } from '@/types/college';
import {
  Building2,
  Check,
  ChevronDown,
  GraduationCap,
  MapPin,
  PlusCircle,
  Search,
  Sparkles,
  X,
} from 'lucide-react';

interface CollegeSelectorProps {
  selectedCollegeId?: string | null;
  onSelectCollege: (college: College | null) => void;
  onCustomCollegeChange?: (customName: string, customLocation: string) => void;
  disabled?: boolean;
  required?: boolean;
  label?: string;
}

const CATEGORY_FILTERS = [
  'All',
  'Engineering & Technology',
  'Arts & Science',
  'Medical & Allied Health',
  'Management',
  'Polytechnic',
  'University',
];

export const CollegeSelector: React.FC<CollegeSelectorProps> = ({
  selectedCollegeId,
  onSelectCollege,
  onCustomCollegeChange,
  disabled = false,
  required = false,
  label = 'Select Your College',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('All');
  const [colleges, setColleges] = useState<College[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCollege, setSelectedCollege] = useState<College | null>(null);

  // Custom "Other / Not Listed" mode
  const [isOtherSelected, setIsOtherSelected] = useState(false);
  const [customName, setCustomName] = useState('');
  const [customLocation, setCustomLocation] = useState('');

  const containerRef = useRef<HTMLDivElement | null>(null);
  const searchInputRef = useRef<HTMLInputElement | null>(null);

  // Fetch initial top colleges or search as user types
  useEffect(() => {
    let active = true;
    const fetchColleges = async () => {
      setIsLoading(true);
      try {
        const trimmed = searchTerm.trim();
        let endpoint = '/colleges?district=Coimbatore&page_size=40';
        if (trimmed) {
          endpoint = `/colleges/search?q=${encodeURIComponent(trimmed)}&limit=30`;
        } else if (selectedType !== 'All') {
          endpoint = `/colleges?type=${encodeURIComponent(selectedType)}&page_size=40`;
        }

        const res = await api.get<College[]>(endpoint);
        if (active) {
          setColleges(res || []);
        }
      } catch {
        if (active) setColleges([]);
      } finally {
        if (active) setIsLoading(false);
      }
    };

    const timer = setTimeout(fetchColleges, searchTerm ? 250 : 0);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [searchTerm, selectedType]);

  // Load initially selected college details if ID passed
  useEffect(() => {
    if (!selectedCollegeId) {
      if (!isOtherSelected) {
        setSelectedCollege(null);
      }
      return;
    }
    const loadSelected = async () => {
      try {
        const college = await api.get<College>(`/colleges/${selectedCollegeId}`);
        if (college) {
          setSelectedCollege(college);
          setIsOtherSelected(false);
        }
      } catch {
        // Fallback
      }
    };
    loadSelected();
  }, [selectedCollegeId]);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (college: College) => {
    setSelectedCollege(college);
    setIsOtherSelected(false);
    setCustomName('');
    setCustomLocation('');
    onSelectCollege(college);
    if (onCustomCollegeChange) onCustomCollegeChange('', '');
    setIsOpen(false);
  };

  const handleChooseOther = () => {
    setIsOtherSelected(true);
    setSelectedCollege(null);
    onSelectCollege(null);
    setIsOpen(false);
  };

  const handleCustomInputChange = (nameVal: string, locVal: string) => {
    setCustomName(nameVal);
    setCustomLocation(locVal);
    if (onCustomCollegeChange) {
      onCustomCollegeChange(nameVal, locVal);
    }
  };

  const clearSelection = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedCollege(null);
    setIsOtherSelected(false);
    setCustomName('');
    setCustomLocation('');
    onSelectCollege(null);
    if (onCustomCollegeChange) onCustomCollegeChange('', '');
    setSearchTerm('');
  };

  return (
    <div ref={containerRef} style={{ display: 'flex', flexDirection: 'column', gap: '6px', position: 'relative' }}>
      {/* Field Label */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
          {label} {required && <span style={{ color: 'var(--status-danger)' }}>*</span>}
        </label>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Coimbatore District</span>
      </div>

      {/* Selected Box / Trigger Button */}
      {!isOtherSelected ? (
        <div
          onClick={() => {
            if (!disabled) {
              setIsOpen(!isOpen);
              setTimeout(() => searchInputRef.current?.focus(), 100);
            }
          }}
          style={{
            minHeight: '44px',
            padding: '8px 14px',
            borderRadius: 'var(--radius-md)',
            border: isOpen ? '1px solid var(--brand-primary)' : '1px solid var(--border-default)',
            backgroundColor: disabled ? 'var(--bg-surface-subtle)' : 'var(--bg-surface)',
            boxShadow: isOpen ? '0 0 0 3px rgba(79, 70, 229, 0.15)' : 'var(--shadow-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: disabled ? 'not-allowed' : 'pointer',
            transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
          }}
        >
          {selectedCollege ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0, flex: 1 }}>
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '6px',
                  backgroundColor: 'rgba(79, 70, 229, 0.1)',
                  color: 'var(--brand-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <GraduationCap size={16} />
              </div>
              <div style={{ minWidth: 0, flex: 1 }}>
                <div
                  style={{
                    fontSize: '13px',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {selectedCollege.name}
                </div>
                <div
                  style={{
                    fontSize: '11px',
                    color: 'var(--text-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    marginTop: '2px',
                  }}
                >
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '2px' }}>
                    <MapPin size={10} color="var(--text-muted)" />
                    {selectedCollege.location}
                  </span>
                  <span>•</span>
                  <span>{selectedCollege.institution_type}</span>
                </div>
              </div>
              <button
                type="button"
                onClick={clearSelection}
                title="Clear selection"
                style={{
                  border: 'none',
                  background: 'transparent',
                  cursor: 'pointer',
                  color: 'var(--text-muted)',
                  padding: '4px',
                  borderRadius: '4px',
                }}
              >
                <X size={14} />
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '13px' }}>
              <Building2 size={16} color="var(--text-muted)" />
              <span>Search & select college in Coimbatore...</span>
            </div>
          )}

          <ChevronDown
            size={16}
            color="var(--text-muted)"
            style={{
              transition: 'transform 0.2s ease',
              transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
              flexShrink: 0,
              marginLeft: '8px',
            }}
          />
        </div>
      ) : (
        /* "Other / College Not Listed" Entry Mode */
        <div
          style={{
            padding: '16px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-default)',
            backgroundColor: 'var(--bg-surface-subtle)',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--brand-primary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Sparkles size={14} /> Unlisted College Request
            </span>
            <button
              type="button"
              onClick={() => {
                setIsOtherSelected(false);
                setCustomName('');
                setCustomLocation('');
                if (onCustomCollegeChange) onCustomCollegeChange('', '');
              }}
              style={{
                fontSize: '11px',
                color: 'var(--text-muted)',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                textDecoration: 'underline',
              }}
            >
              Back to college search
            </button>
          </div>

          <div>
            <label style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px', display: 'block' }}>
              Enter Full College Name *
            </label>
            <input
              type="text"
              placeholder="e.g. United Institute of Technology, Coimbatore"
              value={customName}
              onChange={(e) => handleCustomInputChange(e.target.value, customLocation)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-default)',
                fontSize: '13px',
                backgroundColor: 'var(--bg-surface)',
                color: 'var(--text-primary)',
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px', display: 'block' }}>
              Campus Location / Area in Coimbatore
            </label>
            <input
              type="text"
              placeholder="e.g. Periyanaickenpalayam, Coimbatore"
              value={customLocation}
              onChange={(e) => handleCustomInputChange(customName, e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                border: '1px solid var(--border-default)',
                fontSize: '13px',
                backgroundColor: 'var(--bg-surface)',
                color: 'var(--text-primary)',
              }}
            />
          </div>
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: 0 }}>
            This college will be submitted for institutional administrative review and verified.
          </p>
        </div>
      )}

      {/* Floating Dropdown Modal / List */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            zIndex: 50,
            marginTop: '6px',
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-subtle)',
            boxShadow: 'var(--shadow-lg)',
            padding: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
            maxHeight: '440px',
          }}
        >
          {/* Search Input Bar */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 12px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-default)',
              backgroundColor: 'var(--bg-surface-subtle)',
            }}
          >
            <Search size={16} color="var(--text-muted)" />
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Type college name, code, or keyword (e.g. PSG, CIT, Krishna, KCT)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                flex: 1,
                border: 'none',
                background: 'transparent',
                outline: 'none',
                fontSize: '13px',
                color: 'var(--text-primary)',
              }}
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm('')}
                style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Quick Category Chips */}
          <div
            style={{
              display: 'flex',
              gap: '6px',
              overflowX: 'auto',
              paddingBottom: '4px',
              scrollbarWidth: 'none',
            }}
          >
            {CATEGORY_FILTERS.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedType(cat)}
                style={{
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-full)',
                  border: selectedType === cat ? '1px solid var(--brand-primary)' : '1px solid var(--border-subtle)',
                  backgroundColor: selectedType === cat ? 'var(--brand-primary-subtle)' : 'var(--bg-surface)',
                  color: selectedType === cat ? 'var(--brand-primary)' : 'var(--text-secondary)',
                  fontSize: '11px',
                  fontWeight: selectedType === cat ? 600 : 500,
                  whiteSpace: 'nowrap',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* College Results Scrollable List */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              maxHeight: '260px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
            }}
          >
            {isLoading ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
                Searching Coimbatore colleges...
              </div>
            ) : colleges.length === 0 ? (
              <div style={{ padding: '20px', textAlign: 'center' }}>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: '0 0 8px 0' }}>
                  No college found matching &ldquo;{searchTerm}&rdquo;
                </p>
                <button
                  type="button"
                  onClick={handleChooseOther}
                  style={{
                    fontSize: '12px',
                    color: 'var(--brand-primary)',
                    background: 'var(--brand-primary-subtle)',
                    border: '1px solid var(--brand-primary)',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontWeight: 600,
                  }}
                >
                  + Add &ldquo;{searchTerm}&rdquo; as unlisted college
                </button>
              </div>
            ) : (
              colleges.map((col) => {
                const isSelected = selectedCollege?.id === col.id;
                return (
                  <div
                    key={col.id}
                    onClick={() => handleSelect(col)}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: isSelected ? 'var(--brand-primary-subtle)' : 'transparent',
                      border: isSelected ? '1px solid var(--brand-primary)' : '1px solid transparent',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '10px',
                      transition: 'background-color 0.12s ease',
                    }}
                    onMouseEnter={(e) => {
                      if (!isSelected) e.currentTarget.style.backgroundColor = 'var(--bg-surface-subtle)';
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelected) e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                  >
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                          {col.name}
                        </span>
                        {col.code && (
                          <span
                            style={{
                              fontSize: '10px',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              backgroundColor: 'var(--border-subtle)',
                              color: 'var(--text-secondary)',
                              fontWeight: 600,
                            }}
                          >
                            Code: {col.code}
                          </span>
                        )}
                      </div>
                      <div
                        style={{
                          fontSize: '11px',
                          color: 'var(--text-secondary)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          marginTop: '3px',
                          flexWrap: 'wrap',
                        }}
                      >
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '2px' }}>
                          <MapPin size={11} color="var(--text-muted)" />
                          {col.location}, {col.district}
                        </span>
                        <span>•</span>
                        <span style={{ color: 'var(--brand-primary)', fontWeight: 500 }}>
                          {col.institution_type}
                        </span>
                        {col.accreditation && (
                          <>
                            <span>•</span>
                            <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
                              {col.accreditation.split('|')[0]}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                    {isSelected && <Check size={16} color="var(--brand-primary)" style={{ flexShrink: 0 }} />}
                  </div>
                );
              })
            )}
          </div>

          {/* Footer Option: Other / College Not Listed */}
          <div
            style={{
              paddingTop: '8px',
              borderTop: '1px solid var(--border-subtle)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Showing verified institutions in Coimbatore
            </span>
            <button
              type="button"
              onClick={handleChooseOther}
              style={{
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--brand-primary)',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 8px',
                borderRadius: '4px',
              }}
            >
              <PlusCircle size={13} />
              Other / College Not Listed
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

