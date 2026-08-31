/**
 * Browser Compatibility Check for Animated Background
 * Checks if browser supports backdrop-filter and other required features
 */

export const checkBackdropFilterSupport = () => {
  // Check for standard backdrop-filter
  if (CSS.supports('backdrop-filter', 'blur(20px)')) {
    return { supported: true, prefix: 'standard' };
  }
  
  // Check for webkit prefix (Safari)
  if (CSS.supports('-webkit-backdrop-filter', 'blur(20px)')) {
    return { supported: true, prefix: 'webkit' };
  }
  
  return { supported: false, prefix: null };
};

export const checkAnimationSupport = () => {
  return CSS.supports('animation', 'test 1s linear');
};

export const checkTransformSupport = () => {
  return CSS.supports('transform', 'translate(0, 0)');
};

export const getBrowserInfo = () => {
  const ua = navigator.userAgent;
  let browserName = 'Unknown';
  let browserVersion = 'Unknown';
  
  // Chrome
  if (ua.indexOf('Chrome') > -1 && ua.indexOf('Edg') === -1) {
    browserName = 'Chrome';
    const match = ua.match(/Chrome\/(\d+)/);
    if (match) browserVersion = match[1];
  }
  // Edge
  else if (ua.indexOf('Edg') > -1) {
    browserName = 'Edge';
    const match = ua.match(/Edg\/(\d+)/);
    if (match) browserVersion = match[1];
  }
  // Firefox
  else if (ua.indexOf('Firefox') > -1) {
    browserName = 'Firefox';
    const match = ua.match(/Firefox\/(\d+)/);
    if (match) browserVersion = match[1];
  }
  // Safari
  else if (ua.indexOf('Safari') > -1 && ua.indexOf('Chrome') === -1) {
    browserName = 'Safari';
    const match = ua.match(/Version\/(\d+)/);
    if (match) browserVersion = match[1];
  }
  
  return { name: browserName, version: browserVersion };
};

export const checkBrowserCompatibility = () => {
  const backdropFilter = checkBackdropFilterSupport();
  const animations = checkAnimationSupport();
  const transforms = checkTransformSupport();
  const browser = getBrowserInfo();
  
  // Check minimum versions
  let meetsMinimum = true;
  let reason = '';
  
  if (browser.name === 'Chrome' && parseInt(browser.version) < 76) {
    meetsMinimum = false;
    reason = 'Chrome version must be 76 or higher (2019+)';
  } else if (browser.name === 'Edge' && parseInt(browser.version) < 76) {
    meetsMinimum = false;
    reason = 'Edge version must be 76 or higher (2019+)';
  } else if (browser.name === 'Firefox' && parseInt(browser.version) < 103) {
    meetsMinimum = false;
    reason = 'Firefox version must be 103 or higher (2022+)';
  } else if (browser.name === 'Safari' && parseInt(browser.version) < 9) {
    meetsMinimum = false;
    reason = 'Safari version must be 9 or higher (2015+)';
  }
  
  return {
    compatible: backdropFilter.supported && animations && transforms && meetsMinimum,
    features: {
      backdropFilter: backdropFilter.supported,
      backdropFilterPrefix: backdropFilter.prefix,
      animations,
      transforms,
    },
    browser,
    meetsMinimum,
    reason,
  };
};

export const showCompatibilityWarning = () => {
  const result = checkBrowserCompatibility();
  
  if (!result.compatible) {
    console.warn('⚠️ Browser Compatibility Issue:');
    console.warn(`Browser: ${result.browser.name} ${result.browser.version}`);
    console.warn(`Backdrop Filter: ${result.features.backdropFilter ? '✓' : '✗'}`);
    console.warn(`Animations: ${result.features.animations ? '✓' : '✗'}`);
    console.warn(`Transforms: ${result.features.transforms ? '✓' : '✗'}`);
    
    if (!result.meetsMinimum) {
      console.warn(`⚠️ ${result.reason}`);
    }
    
    if (!result.features.backdropFilter) {
      console.warn('💡 Glass morphism effects may not work. Update your browser or enable hardware acceleration.');
    }
    
    return true;
  }
  
  console.log('✅ Browser fully supports animated background features');
  console.log(`Browser: ${result.browser.name} ${result.browser.version}`);
  if (result.features.backdropFilterPrefix === 'webkit') {
    console.log('ℹ️ Using -webkit- prefix for backdrop-filter');
  }
  
  return false;
};

export const getPerformanceRecommendations = () => {
  const recommendations = [];
  
  // Check if GPU acceleration is available
  const canvas = document.createElement('canvas');
  const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
  
  if (!gl) {
    recommendations.push({
      level: 'warning',
      message: 'WebGL not detected. Hardware acceleration may be disabled.',
      action: 'Enable hardware acceleration in browser settings.',
    });
  }
  
  // Check memory
  if (performance.memory) {
    const usedMemoryMB = performance.memory.usedJSHeapSize / 1048576;
    if (usedMemoryMB > 500) {
      recommendations.push({
        level: 'info',
        message: `High memory usage detected (${usedMemoryMB.toFixed(0)}MB)`,
        action: 'Close unused tabs for better performance.',
      });
    }
  }
  
  return recommendations;
};

// Debug mode: Log all info to console
export const debugBrowserInfo = () => {
  console.group('🔍 Browser & Feature Detection');
  
  const compat = checkBrowserCompatibility();
  console.log('Compatible:', compat.compatible);
  console.log('Browser:', compat.browser);
  console.log('Features:', compat.features);
  
  if (!compat.meetsMinimum) {
    console.warn('Reason:', compat.reason);
  }
  
  const perf = getPerformanceRecommendations();
  if (perf.length > 0) {
    console.log('Recommendations:', perf);
  }
  
  console.groupEnd();
};
