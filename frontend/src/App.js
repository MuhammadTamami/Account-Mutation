import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import { showCompatibilityWarning, debugBrowserInfo } from './utils/browserCheck';

const API_URL = 'http://localhost:5000';

function App() {
  const [currentPage, setCurrentPage] = useState('home'); // 'home' or 'results'
  const [uploadMode, setUploadMode] = useState(null); // 'full' or 'daily'
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  
  // Results data
  const [allData, setAllData] = useState(null);
  const [dailyBalance, setDailyBalance] = useState(null);
  const [monthlySummary, setMonthlySummary] = useState(null);
  const [summary, setSummary] = useState(null);
  const [tempFile, setTempFile] = useState(null);
  const [accountInfo, setAccountInfo] = useState(null);
  
  // Filters
  const [selectedMonth, setSelectedMonth] = useState('all');
  const [dateFilter, setDateFilter] = useState({ start: '', end: '' });
  const [copySuccess, setCopySuccess] = useState('');

  const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB
  const MAX_BATCH_FILES = 100;

  // Check browser compatibility on mount
  useEffect(() => {
    showCompatibilityWarning();
    // Uncomment for detailed debug info:
    // debugBrowserInfo();
  }, []);

  const handleOpenUpload = (mode) => {
    setUploadMode(mode);
    setShowUploadModal(true);
    setSelectedFiles([]);
    setError(null);
  };

  const handleCloseModal = () => {
    setShowUploadModal(false);
    setSelectedFiles([]);
    setError(null);
  };

  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    validateAndSetFiles(files);
  };

  const validateAndSetFiles = (files) => {
    // Check batch limit
    if (files.length > MAX_BATCH_FILES) {
      setError(`Maximum ${MAX_BATCH_FILES} files per batch`);
      return;
    }

    // Check file sizes and types
    const validFiles = [];
    for (const file of files) {
      if (file.size > MAX_FILE_SIZE) {
        setError(`File ${file.name} terlalu besar. Max 20MB per file`);
        return;
      }
      
      const fileName = file.name.toLowerCase();
      if (!fileName.endsWith('.csv') && !fileName.endsWith('.pdf') && 
          !fileName.endsWith('.jpg') && !fileName.endsWith('.jpeg') && 
          !fileName.endsWith('.png') && !fileName.endsWith('.xlsx') && 
          !fileName.endsWith('.xls')) {
        setError(`File ${file.name} tidak didukung. Gunakan CSV, PDF, Excel, atau Image`);
        return;
      }
      
      validFiles.push(file);
    }

    setSelectedFiles(validFiles);
    setError(null);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files);
      validateAndSetFiles(files);
    }
  };

  const handleProcess = async () => {
    if (selectedFiles.length === 0) {
      setError('Pilih file terlebih dahulu');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    
    if (selectedFiles.length === 1) {
      formData.append('file', selectedFiles[0]);
    } else {
      selectedFiles.forEach(file => {
        formData.append('files', file);
      });
    }

    try {
      const response = await axios.post(`${API_URL}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Check if IDEB mode
      if (response.data.mode === 'ideb') {
        // IDEB-specific data structure
        setAllData(response.data.data);  // IDEB credit data
        setDailyBalance([]);  // No daily balance for IDEB
        setMonthlySummary([]);  // No monthly summary for IDEB
        setSummary(response.data.summary);
        setTempFile(response.data.tempFile);
        setAccountInfo(null);
        setUploadMode('ideb');  // Set upload mode to IDEB
      } else {
        // Normal bank statement data
        setAllData(response.data.allData);
        setDailyBalance(response.data.dailyBalance);
        setMonthlySummary(response.data.monthlySummary);
        setSummary(response.data.summary);
        setTempFile(response.data.tempFile);
        setAccountInfo(response.data.accountInfo || null);
      }
      
      // Switch to results page
      setCurrentPage('results');
      setShowUploadModal(false);
      
    } catch (err) {
      setError(err.response?.data?.error || 'Terjadi kesalahan saat memproses file');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (format) => {
    if (!tempFile) return;

    setLoading(true);
    try {
      const response = await axios.post(
        `${API_URL}/api/download/${format}`,
        { 
          tempFile,
          mode: uploadMode,  // Send mode to backend
          filters: {         // Send filter parameters
            month: selectedMonth,
            dateStart: dateFilter.start,
            dateEnd: dateFilter.end
          }
        },
        { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Set filename based on mode and filter
      const modeLabel = uploadMode === 'full' ? 'full_scan' : 'daily_balance';
      let filterLabel = '';
      
      if (selectedMonth !== 'all') {
        const monthObj = getAvailableMonths().find(m => m.value === selectedMonth);
        if (monthObj) {
          filterLabel = `_${monthObj.label.replace(/\s+/g, '_')}`;
        }
      } else if (dateFilter.start || dateFilter.end) {
        filterLabel = '_filtered';
      }
      
      link.setAttribute('download', `mutrek_${modeLabel}${filterLabel}.${format === 'excel' ? 'xlsx' : format}`);
      
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('Gagal mengunduh file');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToHome = () => {
    setCurrentPage('home');
    setSelectedFiles([]);
    setAllData(null);
    setDailyBalance(null);
    setMonthlySummary(null);
    setSummary(null);
    setAccountInfo(null);
    setSelectedMonth('all');
    setDateFilter({ start: '', end: '' });
  };

  const formatCurrency = (amount) => {
    if (typeof amount === 'string') return amount;
    // International format: 18,000,000.00 (comma for thousands, dot for decimal)
    const formatted = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
    return formatted;
  };

  const parseIndonesianNumber = (value) => {
    if (!value || value === '-') return 0;
    if (typeof value === 'number') return value;
    
    // International format: 18,000,000.00 (comma for thousands, dot for decimal)
    const str = String(value).trim();
    
    // Remove commas (thousand separators) and parse
    const cleaned = str.replace(/,/g, '');
    return parseFloat(cleaned) || 0;
  };

  const getAvailableMonths = () => {
    if (!dailyBalance) return [];
    const months = dailyBalance.map(row => {
      const date = new Date(row.Date);
      return {
        value: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`,
        label: date.toLocaleDateString('id-ID', { year: 'numeric', month: 'long' })
      };
    });
    return Array.from(new Map(months.map(m => [m.value, m])).values());
  };

  const getFilteredData = () => {
    if (!allData) return [];
    let filtered = allData;

    // Filter by month
    if (selectedMonth !== 'all') {
      filtered = filtered.filter(row => {
        const date = new Date(row.Date);
        const rowMonth = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        return rowMonth === selectedMonth;
      });
    }

    // Filter by date range
    if (dateFilter.start) {
      filtered = filtered.filter(row => new Date(row.Date) >= new Date(dateFilter.start));
    }
    if (dateFilter.end) {
      filtered = filtered.filter(row => new Date(row.Date) <= new Date(dateFilter.end));
    }

    return filtered;
  };

  const getFilteredDailyBalance = () => {
    if (!dailyBalance) return [];
    let filtered = dailyBalance;

    // Filter by month
    if (selectedMonth !== 'all') {
      filtered = filtered.filter(row => {
        const date = new Date(row.Date);
        const rowMonth = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
        return rowMonth === selectedMonth;
      });
    }

    // Filter by date range
    if (dateFilter.start) {
      filtered = filtered.filter(row => new Date(row.Date) >= new Date(dateFilter.start));
    }
    if (dateFilter.end) {
      filtered = filtered.filter(row => new Date(row.Date) <= new Date(dateFilter.end));
    }

    return filtered;
  };

  const getFilteredStats = () => {
    const filtered = getFilteredData();
    const debitCount = filtered.filter(r => r.Type === 'Debit').length;
    const creditCount = filtered.filter(r => r.Type === 'Credit').length;
    const totalDebit = filtered
      .filter(r => r.Type === 'Debit')
      .reduce((sum, r) => sum + parseIndonesianNumber(r.Amount), 0);
    const totalCredit = filtered
      .filter(r => r.Type === 'Credit')
      .reduce((sum, r) => sum + parseIndonesianNumber(r.Amount), 0);

    return { debitCount, creditCount, totalDebit, totalCredit };
  };

  // HOME PAGE
  if (currentPage === 'home') {
    return (
      <div className="App">
        {/* Animated 3D Background */}
        <div className="animated-background">
          {/* Grid Lines */}
          <div className="grid-lines"></div>
          
          {/* Floating Documents */}
          <div className="floating-doc">📄</div>
          <div className="floating-doc">📊</div>
          <div className="floating-doc">📈</div>
          <div className="floating-doc">📋</div>
          <div className="floating-doc">📑</div>
          <div className="floating-doc">📉</div>
          <div className="floating-doc">📃</div>
          <div className="floating-doc">🗂️</div>
          
          {/* Glowing Particles */}
          <div className="particle"></div>
          <div className="particle"></div>
          <div className="particle"></div>
          <div className="particle"></div>
          <div className="particle"></div>
        </div>

        {/* Navbar */}
        <nav className="navbar">
          <div className="navbar-brand">
            <h1>MURENA</h1>
          </div>
          <div className="navbar-description">
            <p>📊 Analisis Mutasi Rekening</p>
            <p>💰 Tracking Keuangan Otomatis</p>
            <p>📈 Statistik Real-time</p>
          </div>
        </nav>

        <div className="container home-container">
          {/* Hero Section */}
          <section className="hero-section">
            <h2 className="hero-title">Kelola Mutasi Rekening Anda dengan Mudah</h2>
            <p className="hero-subtitle">Upload, Analisis, dan Dapatkan Insight dalam Hitungan Detik</p>
          </section>

          {/* Main Content: 2 Column Layout */}
          <div className="main-content-layout">
            {/* Left Column: 3 Main Cards */}
            <div className="main-cards-column">
              {/* Card 1: Full Scan */}
              <div className="feature-card">
                <div className="card-icon">📊</div>
                <h3 className="card-title">Full Scan Mutrek</h3>
                <p className="card-description">
                  Analisis lengkap semua transaksi dengan breakdown per bulan
                </p>
                
                <div className="card-tutorial">
                  <h4>📝 Cara Pakai:</h4>
                  <ol>
                    <li>Klik button "Upload File"</li>
                    <li>Pilih/drag file mutrek (CSV, PDF, Excel, Image)</li>
                    <li>Klik "Proses" dan tunggu sebentar</li>
                    <li>Lihat hasil analisis lengkap</li>
                  </ol>
                </div>

                <button 
                  className="card-action-btn"
                  onClick={() => handleOpenUpload('full')}
                >
                  <span className="btn-icon">📤</span>
                  Upload File
                </button>
              </div>

              {/* Card 2: Daily Balance */}
              <div className="feature-card">
                <div className="card-icon">📅</div>
                <h3 className="card-title">Cek Saldo Terakhir</h3>
                <p className="card-description">
                  Monitor saldo akhir hari untuk tracking harian
                </p>
                
                <div className="card-tutorial">
                  <h4>📝 Cara Pakai:</h4>
                  <ol>
                    <li>Klik button "Upload File"</li>
                    <li>Pilih/drag file mutrek (semua format OK)</li>
                    <li>Klik "Proses" dan tunggu sebentar</li>
                    <li>Lihat saldo penutupan per hari</li>
                  </ol>
                </div>

                <button 
                  className="card-action-btn"
                  onClick={() => handleOpenUpload('daily')}
                >
                  <span className="btn-icon">📤</span>
                  Upload File
                </button>
              </div>

              {/* Card 3: IDEB SLIK */}
              <div className="feature-card">
                <div className="card-icon">📋</div>
                <h3 className="card-title">IDEB SLIK Analyzer</h3>
                <p className="card-description">
                  Analisis data kredit/pinjaman dari IDEB SLIK (Baki Debet &gt; 0)
                </p>
                
                <div className="card-tutorial">
                  <h4>📝 Cara Pakai:</h4>
                  <ol>
                    <li>Klik button "Upload IDEB"</li>
                    <li>Pilih/drag file IDEB PDF</li>
                    <li>Klik "Proses" dan tunggu</li>
                    <li>Lihat data kredit dengan Baki Debet &gt; 0</li>
                  </ol>
                </div>

                <button 
                  className="card-action-btn"
                  onClick={() => handleOpenUpload('ideb')}
                >
                  <span className="btn-icon">📤</span>
                  Upload IDEB
                </button>
              </div>
            </div>

            {/* Right Column: Latest Features */}
            <div className="features-column">
              <div className="latest-features-card">
                <h3 className="section-title">
                  <span className="badge-new">v2.1.0</span>
                  Changelog & Fitur Terbaru
                </h3>
                
                <div className="changelog-section">
                  <h4 className="changelog-version">🎉 Version 2.1.0 (Sep 2026)</h4>
                  <div className="feature-item-mini highlight">
                    <span className="feature-icon-mini">✨</span>
                    <div>
                      <strong>Balance-Based Detection</strong>
                      <p>Semua transaksi (monthly fee, admin fee, tax, dll) PASTI terdeteksi sebagai Debit/Kredit tanpa bergantung keyword</p>
                    </div>
                  </div>
                  <div className="feature-item-mini highlight">
                    <span className="feature-icon-mini">📊</span>
                    <div>
                      <strong>100% Accurate Mutation Stats</strong>
                      <p>Total Mutasi Debet/Kredit & Freq Debet/Kredit sekarang 100% akurat untuk Bank Kalsel, Mandiri, BSI, dan BRI</p>
                    </div>
                  </div>
                </div>

                <div className="changelog-section ongoing-section">
                  <h4 className="changelog-version">
                    ✅ Production Ready
                    <span className="badge-ready">LIVE</span>
                  </h4>
                  <div className="feature-item-mini ready">
                    <span className="feature-icon-mini">🤖</span>
                    <div>
                      <strong>Bot Telegram - MURENA</strong>
                      <p>Upload mutrek langsung dari Telegram, auto-processing 7+ bank, download hasil Excel/CSV via bot</p>
                      <p className="bot-features">
                        ✓ Full Scan (semua transaksi) | ✓ Daily Balance (saldo harian + statistik) | ✓ IDEB SLIK (analisis kredit)
                      </p>
                    </div>
                  </div>
                  <div className="ready-note">
                    <small>🎉 <em>Bot sudah aktif! Hubungi admin untuk akses (@murenabank_bot)</em></small>
                  </div>
                </div>

                <div className="changelog-section">
                  <h4 className="changelog-version">Version 2.0.0</h4>
                  <div className="features-list">
                    <div className="feature-item-mini">
                      <span className="feature-icon-mini">🏦</span>
                      <div>
                        <strong>Multi-Bank Support</strong>
                        <p>BSI, Mandiri, BCA, BRI, BNI, Bank Kalsel</p>
                      </div>
                    </div>

                    <div className="feature-item-mini">
                      <span className="feature-icon-mini">📋</span>
                      <div>
                        <strong>IDEB SLIK Analyzer</strong>
                        <p>Analisis kredit/pinjaman (Baki Debet &gt; 0)</p>
                      </div>
                    </div>

                    <div className="feature-item-mini">
                      <span className="feature-icon-mini">📄</span>
                      <div>
                        <strong>Multi-Format</strong>
                        <p>CSV, PDF, Excel, Image (OCR)</p>
                      </div>
                    </div>

                    <div className="feature-item-mini">
                      <span className="feature-icon-mini">🔍</span>
                      <div>
                        <strong>Smart Filter Download</strong>
                        <p>Download sesuai filter aktif</p>
                      </div>
                    </div>

                    <div className="feature-item-mini">
                      <span className="feature-icon-mini">📊</span>
                      <div>
                        <strong>Statistik Real-time</strong>
                        <p>Filter per bulan & tanggal</p>
                      </div>
                    </div>

                    <div className="feature-item-mini">
                      <span className="feature-icon-mini">📤</span>
                      <div>
                        <strong>Batch Upload</strong>
                        <p>Hingga 100 file sekaligus</p>
                      </div>
                    </div>

                    <div className="feature-item-mini">
                      <span className="feature-icon-mini">🔐</span>
                      <div>
                        <strong>Password-Protected PDF</strong>
                        <p>Mandiri e-Statement dengan password</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Section: Info & Spesifikasi */}
          <div className="info-specs-section">
            <h3 className="section-title">📋 Informasi & Spesifikasi</h3>
            
            <div className="specs-grid">
              <div className="spec-card">
                <h4>🏦 Bank yang Didukung</h4>
                <p>BSI • Mandiri • BCA • BRI • BNI • Bank Kalsel</p>
                <span className="spec-badge">6 Banks + Auto-detect</span>
              </div>

              <div className="spec-card">
                <h4>📋 IDEB SLIK</h4>
                <p>Analisis kredit/pinjaman • Filter Baki Debet &gt; 0</p>
                <span className="spec-badge">NEW!</span>
              </div>

              <div className="spec-card">
                <h4>💾 Format File</h4>
                <p>CSV • PDF • Excel • Image (OCR)</p>
                <span className="spec-badge">All formats</span>
              </div>

              <div className="spec-card">
                <h4>⚙️ Limit & Batasan</h4>
                <p>Max 20MB per file • Max 100 files batch</p>
                <span className="spec-badge">Fast processing</span>
              </div>

              <div className="spec-card">
                <h4>📊 Fitur Analisis</h4>
                <p>Statistik • Filter • Export • Monthly Summary</p>
                <span className="spec-badge">Real-time</span>
              </div>

              <div className="spec-card">
                <h4>🔒 Keamanan</h4>
                <p>Proses lokal • No cloud storage • Private</p>
                <span className="spec-badge">100% Secure</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="footer">
          <div className="footer-content">
            <div className="footer-brand">
              <h3>MUTREK</h3>
              <p>Analisis Mutasi Rekening</p>
            </div>
            <div className="footer-info">
              <p>© 2026 Tama. All rights reserved.</p>
              <p className="footer-version">Version 2.1.0 - Balance-Based Detection</p>
              <p className="footer-bot-status">🤖 Bot Telegram MURENA: <span className="status-live">✅ LIVE & Running</span></p>
              <p className="footer-tagline">Built with 💚 for better financial tracking</p>
            </div>
          </div>
        </footer>

        {/* Upload Modal */}
        {showUploadModal && (
          <div className="modal-overlay" onClick={handleCloseModal}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>
                  {uploadMode === 'full' ? '📊 Upload untuk Full Scan' : 
                   uploadMode === 'ideb' ? '📋 Upload IDEB SLIK PDF' : 
                   '📅 Upload untuk Cek Saldo'}
                </h3>
                <button className="modal-close" onClick={handleCloseModal}>×</button>
              </div>

              <div className="modal-body">
                <div 
                  className={`dropzone ${dragActive ? 'active' : ''}`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  <div className="dropzone-content">
                    <div className="dropzone-icon">📁</div>
                    <h4>Drag & Drop File Di Sini</h4>
                    <p>atau</p>
                    <label className="file-select-label">
                      <input
                        type="file"
                        accept=".csv,.pdf,.jpg,.jpeg,.png,.xlsx,.xls"
                        onChange={handleFileSelect}
                        multiple
                        style={{ display: 'none' }}
                      />
                      Pilih File
                    </label>
                    <p className="dropzone-hint">
                      Max 20MB per file | Max 100 files | CSV, PDF, Excel, JPG, PNG
                    </p>
                  </div>
                </div>

                {selectedFiles.length > 0 && (
                  <div className="selected-files-box">
                    <h4>File Terpilih ({selectedFiles.length}):</h4>
                    <ul className="files-list">
                      {selectedFiles.map((file, idx) => (
                        <li key={idx} className="file-item">
                          <span className="file-name">{file.name}</span>
                          <span className="file-size">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {error && (
                  <div className="error-box">
                    <span className="error-icon">⚠</span>
                    {error}
                  </div>
                )}
              </div>

              <div className="modal-footer">
                <button className="btn-secondary" onClick={handleCloseModal}>
                  Batal
                </button>
                <button 
                  className="btn-primary" 
                  onClick={handleProcess}
                  disabled={selectedFiles.length === 0 || loading}
                >
                  {loading ? (
                    <><span className="spinner"></span> Memproses...</>
                  ) : (
                    <>Proses {selectedFiles.length} File</>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // RESULTS PAGE
  return (
    <div className="App results-page">
      {/* Animated 3D Background */}
      <div className="animated-background">
        {/* Grid Lines */}
        <div className="grid-lines"></div>
        
        {/* Floating Documents */}
        <div className="floating-doc">📄</div>
        <div className="floating-doc">📊</div>
        <div className="floating-doc">📈</div>
        <div className="floating-doc">📋</div>
        <div className="floating-doc">📑</div>
        
        {/* Glowing Particles */}
        <div className="particle"></div>
        <div className="particle"></div>
        <div className="particle"></div>
      </div>

      {/* Results Navbar */}
      <nav className="navbar navbar-results">
        <div className="navbar-brand">
          <h1>MUTREK</h1>
        </div>
        <button className="btn-back" onClick={handleBackToHome}>
          ← Kembali ke Home
        </button>
      </nav>

      <div className="container results-container">
        <h2 className="results-title">
          {uploadMode === 'full' ? '📊 Hasil Full Scan' : 
           uploadMode === 'ideb' ? '📋 Hasil IDEB SLIK' : 
           '📅 Hasil Cek Saldo'}
        </h2>

        <div className="results-layout">
          {/* Left: Account Info & Results Table */}
          <div className="results-main">
            {/* Card 1: Account Info */}
            <div className="result-card account-info-card">
              <h3 className="result-card-title">👤 Informasi Rekening</h3>
              {accountInfo ? (
                <div className="account-info-grid">
                  <div className="info-row">
                    <span className="info-label">Nama:</span>
                    <span className="info-value">{accountInfo.name || '-'}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">No. Rekening:</span>
                    <span className="info-value">{accountInfo.accountNumber || '-'}</span>
                  </div>
                  <div className="info-row">
                    <span className="info-label">Cabang:</span>
                    <span className="info-value">{accountInfo.branch || '-'}</span>
                  </div>
                </div>
              ) : (
                <p className="no-info">- Tidak ada informasi rekening -</p>
              )}
            </div>

            {/* Card 2: Results Table */}
            <div className="result-card table-card">
              <div className="table-header">
                <h3 className="result-card-title">
                  {uploadMode === 'full' ? '📋 Data Transaksi' : 
                   uploadMode === 'ideb' ? '💳 Data Kredit/Pinjaman' : 
                   '💰 Saldo Harian'}
                </h3>
                
                <div className="table-actions">
                  <button 
                    className="btn-download"
                    onClick={() => handleDownload('csv')}
                  >
                    📄 CSV
                  </button>
                  <button 
                    className="btn-download"
                    onClick={() => handleDownload('excel')}
                  >
                    📊 Excel
                  </button>
                </div>
              </div>

              <div className="table-scroll">
                {uploadMode === 'ideb' && allData ? (
                  // IDEB SLIK Table
                  <table className="results-table">
                    <thead>
                      <tr>
                        <th className="text-center">No</th>
                        <th>Nama Bank</th>
                        <th className="text-right">Plafon</th>
                        <th className="text-right">Yield (%)</th>
                        <th className="text-right">O/S</th>
                        <th>Tanggal Pencairan</th>
                        <th>Tanggal Jatuh Tempo</th>
                        <th className="text-right">Jk Waktu</th>
                        <th className="text-center">Kol</th>
                        <th>Jenis Konsumsi</th>
                        <th className="text-right">Angsuran</th>
                      </tr>
                    </thead>
                    <tbody>
                      {allData.map((row, idx) => (
                        <tr key={idx}>
                          <td className="text-center">{idx + 1}</td>
                          <td>{row['Nama Bank']}</td>
                          <td className="text-right">{row['Plafon']}</td>
                          <td className="text-right">{row['Yield (%)']}</td>
                          <td className="text-right">{row['O/S']}</td>
                          <td>{row['Tanggal Pencairan']}</td>
                          <td>{row['Tanggal Jatuh Tempo']}</td>
                          <td className="text-right">{row['Jk Waktu']}</td>
                          <td className="text-center">{row['Kol']}</td>
                          <td>{row['Jenis Konsumsi']}</td>
                          <td className="text-right">{row['Angsuran']}</td>
                        </tr>
                      ))}
                      {/* Total Row */}
                      <tr className="total-row">
                        <td colSpan="2" className="text-right"><strong>Total</strong></td>
                        <td className="text-right"><strong>
                          {formatCurrency(allData.reduce((sum, row) => sum + parseIndonesianNumber(row['Plafon']), 0))}
                        </strong></td>
                        <td></td>
                        <td className="text-right"><strong>
                          {formatCurrency(allData.reduce((sum, row) => sum + parseIndonesianNumber(row['O/S']), 0))}
                        </strong></td>
                        <td colSpan="5"></td>
                        <td className="text-right"><strong>
                          {formatCurrency(allData.reduce((sum, row) => sum + parseIndonesianNumber(row['Angsuran']), 0))}
                        </strong></td>
                      </tr>
                    </tbody>
                  </table>
                ) : uploadMode === 'full' && allData ? (
                  <table className="results-table">
                    <thead>
                      <tr>
                        <th>Tanggal</th>
                        <th>Deskripsi</th>
                        <th className="text-right">Debit</th>
                        <th className="text-right">Kredit</th>
                        <th className="text-right">Saldo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {getFilteredData().map((row, idx) => (
                        <tr key={idx}>
                          <td>{new Date(row.Date).toLocaleDateString('id-ID')}</td>
                          <td>{row.Description}</td>
                          <td className="text-right debit">
                            {row.Type === 'Debit' ? row.Amount : '-'}
                          </td>
                          <td className="text-right credit">
                            {row.Type === 'Credit' ? row.Amount : '-'}
                          </td>
                          <td className="text-right">{row.Balance}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : dailyBalance ? (
                  <table className="results-table">
                    <thead>
                      <tr>
                        <th>Tanggal</th>
                        <th className="text-right">Saldo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {getFilteredDailyBalance().map((row, idx) => (
                        <tr key={idx}>
                          <td>{new Date(row.Date).toLocaleDateString('id-ID')}</td>
                          <td className="text-right">{row.Balance}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p>Tidak ada data</p>
                )}
              </div>
            </div>
          </div>

          {/* Right: Filters & Stats */}
          <div className="results-sidebar">
            {/* Filters - Hide for IDEB mode */}
            {uploadMode !== 'ideb' && (
              <div className="result-card filter-card">
                <h3 className="result-card-title">🔍 Filter</h3>
              
              <div className="filter-group">
                <label>Filter Bulan:</label>
                <select 
                  value={selectedMonth}
                  onChange={(e) => setSelectedMonth(e.target.value)}
                  className="filter-select"
                >
                  <option value="all">Semua Bulan</option>
                  {getAvailableMonths().map(m => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
              </div>

              <div className="filter-group">
                <label>Tanggal Mulai:</label>
                <input 
                  type="date"
                  value={dateFilter.start}
                  onChange={(e) => setDateFilter({...dateFilter, start: e.target.value})}
                  className="filter-input"
                />
              </div>

              <div className="filter-group">
                <label>Tanggal Akhir:</label>
                <input 
                  type="date"
                  value={dateFilter.end}
                  onChange={(e) => setDateFilter({...dateFilter, end: e.target.value})}
                  className="filter-input"
                />
              </div>

              <button 
                className="btn-reset-filter"
                onClick={() => {
                  setSelectedMonth('all');
                  setDateFilter({ start: '', end: '' });
                }}
              >
                Reset Filter
              </button>
            </div>
            )}

            {/* Statistics - Hide for IDEB mode */}
            {allData && uploadMode !== 'ideb' && (
              <div className="result-card stats-card">
                <h3 className="result-card-title">📈 Statistik</h3>
                
                {uploadMode === 'daily' && (
                  <p className="stats-note">
                    💡 Statistik dari semua transaksi (full mutrek)
                  </p>
                )}
                
                <div className="stat-item">
                  <span className="stat-label">Total Mutasi Debit:</span>
                  <span className="stat-value debit">{formatCurrency(getFilteredStats().totalDebit)}</span>
                </div>

                <div className="stat-item">
                  <span className="stat-label">Total Mutasi Kredit:</span>
                  <span className="stat-value credit">{formatCurrency(getFilteredStats().totalCredit)}</span>
                </div>

                <div className="stat-item">
                  <span className="stat-label">Freq Debit:</span>
                  <span className="stat-value">{getFilteredStats().debitCount} transaksi</span>
                </div>

                <div className="stat-item">
                  <span className="stat-label">Freq Kredit:</span>
                  <span className="stat-value">{getFilteredStats().creditCount} transaksi</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
