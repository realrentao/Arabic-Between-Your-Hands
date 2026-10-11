/* ===========================================================
   《阿拉伯语在你手中》第一册 · 共享脚本
   - 滚动进度条
   - 导航栏滚动变色
   - 移动端导航开合
   - 阿拉伯语发音（speak）
   =========================================================== */

(function () {
  "use strict";

  /* ---------- 滚动进度条 ---------- */
  var progress = document.querySelector(".scroll-progress");
  function updateProgress() {
    var h = document.documentElement;
    var scrolled = h.scrollTop || document.body.scrollTop;
    var height = h.scrollHeight - h.clientHeight;
    var pct = height > 0 ? (scrolled / height) * 100 : 0;
    if (progress) progress.style.width = pct + "%";
  }

  /* ---------- 导航栏滚动变色 ---------- */
  var nav = document.querySelector(".top-nav");
  function updateNav() {
    if (!nav) return;
    if (window.scrollY > 30) nav.classList.add("scrolled");
    else nav.classList.remove("scrolled");
  }

  window.addEventListener("scroll", function () {
    updateProgress();
    updateNav();
  });
  window.addEventListener("resize", updateProgress);
  updateProgress();
  updateNav();

  /* ---------- 移动端导航 ---------- */
  var toggle = document.querySelector(".nav-toggle");
  var links = document.querySelector(".nav-links");
  if (toggle && links) {
    toggle.addEventListener("click", function () {
      links.classList.toggle("open");
    });
    links.addEventListener("click", function (e) {
      if (e.target.tagName === "A") links.classList.remove("open");
    });
  }

  /* ---------- 阿拉伯语发音（edge-tts 真人音频优先 + 浏览器兜底） ---------- */
  var AR_AUDIO = window.AR_AUDIO || {};
  var audioCache = {};

  function normalizeAr(text) {
    return (text || "").replace(/\s+/g, " ").trim();
  }

  function playAudio(url) {
    try {
      var a = audioCache[url];
      if (!a) {
        a = new Audio(url);
        audioCache[url] = a;
      }
      a.currentTime = 0;
      var pr = a.play();
      if (pr && pr.catch) {
        pr.catch(function (e) {
          console.warn("音频播放失败，转浏览器合成:", e);
          synthFallback(normalizeAr(window.__lastArText || ""));
        });
      }
    } catch (e) {
      console.warn("Audio 创建失败:", e);
    }
  }

  function synthFallback(text, lang) {
    if (!("speechSynthesis" in window)) return;
    try {
      window.speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(text);
      u.lang = lang || "ar-SA";
      u.rate = 0.9;
      window.speechSynthesis.speak(u);
    } catch (e) {
      console.warn("兜底合成失败:", e);
    }
  }

  function speak(text, lang) {
    text = normalizeAr(text);
    if (!text) return;
    window.__lastArText = text;
    var url = AR_AUDIO[text];
    if (url) {
      playAudio(url); // 真人音频
    } else {
      synthFallback(text, lang); // 无音频文件时浏览器合成兜底
    }
  }

  // 事件委托：点击任意 .ar 元素发音
  document.addEventListener("click", function (e) {
    var el = e.target.closest ? e.target.closest(".ar") : null;
    if (el) {
      var t = el.getAttribute("data-ar") || el.textContent;
      speak(t);
    }
  });

  // 暴露给全局，便于按钮直接调用
  window.speakArabic = speak;
})();
