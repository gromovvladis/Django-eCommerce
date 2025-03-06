var footerBlocks = document.querySelectorAll('[data-id="footer-block"]');
footerBlocks.forEach(function (footerBlock) {
    var footerTitle = footerBlock.querySelector('[data-id="footer-title"]');
    footerTitle.addEventListener('click', function () {
        if (window.innerWidth < 768) {
            footerBlock.classList.toggle('open');
        }
    });
});