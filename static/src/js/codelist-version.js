$(document).ready(function () {
  $("#js-codelist-table").DataTable({
    paging: false,
  });

  $('a[data-toggle="tab"]').on("click", function () {
    var url = location.href.split("#")[0];

    if ($(this).attr("href") !== "#about") {
      url += $(this).attr("href");
    }

    history.pushState(null, null, url);
  });

  switchToTab();
  window.addEventListener("hashchange", switchToTab);
});

function switchToTab() {
  var hash = location.hash || "#about";
  $('#tab-list a[href="' + hash + '"]').tab("show");
}
