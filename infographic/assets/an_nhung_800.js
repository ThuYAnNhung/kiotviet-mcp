// Tự thu gọn ảnh vuông 800x800 khi nội dung nhiều: cột thông tin tràn, tiêu đề quá 2 dòng
// hoặc chân trang bị cắt ở mép dưới -> thêm class "gon" (chữ nhỏ lại, không dưới mức tối thiểu).
(function () {
  function tran() {
    const cot = document.querySelector('.cot');
    const chan = document.querySelector('.chan');
    const td = document.querySelector('.tieu-de');
    const sp = document.querySelector('.san-pham');
    return (cot && cot.scrollHeight > cot.clientHeight + 2) ||
           (chan && chan.getBoundingClientRect().bottom > innerHeight + 1) ||
           (td && td.clientHeight > parseFloat(getComputedStyle(td).lineHeight) * 2 + 4) ||
           (sp && sp.clientHeight < 300);
  }
  function chay() { if (tran()) document.body.classList.add('gon'); }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(chay); else chay();
})();
