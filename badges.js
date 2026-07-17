// ============================================================================
// badges.js  —  《红警2》风格程序化兵种徽章生成器
// ----------------------------------------------------------------------------
// 思路：红警2 的 HUD 用的就是扁平化、按阵营配色的单位图标。
// 这里不抓取任何版权贴图，而是按 (阵营 side + 原型 proto) 用 SVG 直接绘制，
// 自包含、离线可用、零版权风险，且契合红警2界面美学。
//
//   side 配色: soviet=红  allied=蓝  yuri=紫  other=灰金
//   proto 轮廓: infantry/vehicle/air/naval/structure/animal/nature/ui/support/other
// ============================================================================

const BADGE = (function () {
  // 阵营主色 / 描边 / 高光
  const SIDE_COLORS = {
    soviet: { base: "#b3261e", dark: "#6e1511", light: "#ff5a4d", ring: "#e0483f" },
    allied: { base: "#1f6fb8", dark: "#103a63", light: "#5db4ff", ring: "#3f93e0" },
    yuri:   { base: "#7b3fa0", dark: "#481f63", light: "#c07be0", ring: "#a05fd0" },
    other:  { base: "#8a8270", dark: "#4f4a3e", light: "#cdc4ad", ring: "#b0a589" },
  };

  // 圆形底纹（放射渐变 + 同心环），营造 HUD 风格
  function plate(cx, cy, R, col) {
    const id = "g" + Math.random().toString(36).slice(2, 8);
    return `
      <defs>
        <radialGradient id="${id}" cx="38%" cy="34%" r="72%">
          <stop offset="0%" stop-color="${col.light}" stop-opacity="0.55"/>
          <stop offset="42%" stop-color="${col.base}"/>
          <stop offset="100%" stop-color="${col.dark}"/>
        </radialGradient>
      </defs>
      <circle cx="${cx}" cy="${cy}" r="${R}" fill="url(#${id})"
              stroke="${col.ring}" stroke-width="2.5"/>
      <circle cx="${cx}" cy="${cy}" r="${R - 5}" fill="none"
              stroke="${col.ring}" stroke-width="1" stroke-opacity="0.5"/>
      <circle cx="${cx}" cy="${cy}" r="${R - 11}" fill="none"
              stroke="#000" stroke-width="1" stroke-opacity="0.25"/>`;
  }

  // 各原型的内嵌剪影（白色描边 + 半透明填充，叠加在圆形底纹之上）
  // 所有路径以 50,50 为中心、半径 ~30 的尺度绘制
  function silhouette(proto, col) {
    const s = {
      fill: "#ffffff",
      stroke: "#0b0e0b",
      sw: 2,
      op: 0.92,
    };
    const W = `fill="${s.fill}" fill-opacity="0.9" stroke="${s.stroke}" stroke-width="${s.sw}" stroke-linejoin="round" stroke-linecap="round"`;
    switch (proto) {
      case "infantry": // 步兵：头 + 肩 + 持枪
        return `
          <g ${W}>
            <circle cx="50" cy="32" r="7"/>
            <path d="M36 70 Q36 48 50 46 Q64 48 64 70 Z"/>
            <rect x="60" y="30" width="4" height="34" rx="2"/>
            <rect x="56" y="46" width="14" height="4" rx="2"/>
          </g>`;
      case "vehicle": // 坦克：履带 + 炮塔 + 炮管
        return `
          <g ${W}>
            <rect x="24" y="56" width="52" height="12" rx="3"/>
            <rect x="28" y="59" width="6" height="6" rx="1"/>
            <rect x="40" y="59" width="6" height="6" rx="1"/>
            <rect x="52" y="59" width="6" height="6" rx="1"/>
            <path d="M34 56 L34 42 Q34 36 42 36 L62 36 Q66 36 66 42 L66 56 Z"/>
            <rect x="64" y="40" width="26" height="5" rx="2"/>
          </g>`;
      case "air": // 空军：飞机 + 机翼 + 尾翼
        return `
          <g ${W}>
            <path d="M22 50 L78 50 L70 56 L30 56 Z"/>
            <path d="M40 50 L34 38 L46 44 Z"/>
            <path d="M40 50 L34 62 L46 56 Z"/>
            <path d="M64 50 L72 42 L66 48 Z"/>
            <path d="M64 50 L72 58 L66 52 Z"/>
            <circle cx="55" cy="50" r="4"/>
          </g>`;
      case "naval": // 海军：船体 + 波浪
        return `
          <g ${W}>
            <path d="M26 46 L74 46 L66 64 L34 64 Z"/>
            <rect x="44" y="32" width="12" height="14" rx="2"/>
            <line x1="50" y1="32" x2="50" y2="22"/>
            <path d="M24 70 Q31 66 38 70 T52 70 T66 70 T80 70" fill="none"/>
          </g>`;
      case "structure": // 建筑：城堡/厂房塔楼
        return `
          <g ${W}>
            <rect x="30" y="40" width="40" height="28" rx="2"/>
            <rect x="34" y="48" width="8" height="8"/>
            <rect x="46" y="48" width="8" height="8"/>
            <rect x="58" y="48" width="8" height="8"/>
            <path d="M30 40 L40 30 L50 40 L60 30 L70 40 Z"/>
            <rect x="46" y="24" width="8" height="8"/>
          </g>`;
      case "animal": // 动物：头 + 耳 + 眼
        return `
          <g ${W}>
            <circle cx="50" cy="52" r="16"/>
            <path d="M36 38 L34 24 L46 34 Z"/>
            <path d="M64 38 L66 24 L54 34 Z"/>
            <circle cx="44" cy="50" r="2.5" fill="#0b0e0b" stroke="none"/>
            <circle cx="56" cy="50" r="2.5" fill="#0b0e0b" stroke="none"/>
            <path d="M46 58 Q50 62 54 58" fill="none"/>
          </g>`;
      case "nature": // 自然：太阳 + 山丘/叶
        return `
          <g ${W}>
            <circle cx="50" cy="44" r="11"/>
            <g stroke="#0b0e0b" stroke-width="2">
              <line x1="50" y1="24" x2="50" y2="29"/>
              <line x1="50" y1="59" x2="50" y2="64"/>
              <line x1="30" y1="44" x2="35" y2="44"/>
              <line x1="65" y1="44" x2="70" y2="44"/>
              <line x1="36" y1="30" x2="40" y2="34"/>
              <line x1="64" y1="30" x2="60" y2="34"/>
              <line x1="36" y1="58" x2="40" y2="54"/>
              <line x1="64" y1="58" x2="60" y2="54"/>
            </g>
            <path d="M28 66 Q50 50 72 66 Z" fill="#ffffff" fill-opacity="0.9"/>
          </g>`;
      case "ui": // 界面：喇叭 / 信号
        return `
          <g ${W}>
            <path d="M34 42 L46 42 L58 32 L58 68 L46 58 L34 58 Z"/>
            <path d="M62 40 Q72 50 62 60" fill="none"/>
            <path d="M66 34 Q80 50 66 66" fill="none"/>
          </g>`;
      case "support": // 超级武器：核电站/闪电标志
        return `
          <g ${W}>
            <path d="M52 22 L34 56 L48 56 L46 78 L66 42 L52 42 Z" fill="#ffffff" fill-opacity="0.95"/>
          </g>`;
      default: // other：齿轮
        return `
          <g ${W}>
            <circle cx="50" cy="50" r="14"/>
            <g fill="#0b0e0b" stroke="none">
              <rect x="47" y="30" width="6" height="6"/>
              <rect x="47" y="64" width="6" height="6"/>
              <rect x="30" y="47" width="6" height="6"/>
              <rect x="64" y="47" width="6" height="6"/>
              <rect x="34" y="34" width="6" height="6"/>
              <rect x="60" y="34" width="6" height="6"/>
              <rect x="34" y="60" width="6" height="6"/>
              <rect x="60" y="60" width="6" height="6"/>
            </g>
            <circle cx="50" cy="50" r="6" fill="#0b0e0b" stroke="none"/>
          </g>`;
    }
  }

  /**
   * 生成一枚兵种徽章的 SVG 字符串。
   * @param {string} side  soviet/allied/yuri/other
   * @param {string} proto infantry/vehicle/air/naval/structure/animal/nature/ui/support/other
   * @param {object} [opt] {size, label}
   * @returns {string} SVG markup
   */
  function badge(side, proto, opt) {
    opt = opt || {};
    const size = opt.size || 48;
    const col = SIDE_COLORS[side] || SIDE_COLORS.other;
    const R = 24; // 半径（viewBox 50x50）
    const inner = plate(50, 50, R, col) + silhouette(proto, col);
    return `<svg class="badge" viewBox="0 0 100 100" width="${size}" height="${size}" `
      + `role="img" aria-label="${opt.label || (side + "/" + proto)}" `
      + `style="--side:${col.ring}">`
      + `<g transform="translate(50,50) scale(0.94) translate(-50,-50)">${inner}</g>`
      + `</svg>`;
  }

  return { badge, SIDE_COLORS };
})();

// 浏览器全局暴露
if (typeof window !== "undefined") window.BADGE = BADGE;
if (typeof module !== "undefined") module.exports = BADGE;
