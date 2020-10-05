import { readValueFromPage } from "./utils";
import Hierarchy from "./hierarchy";
import Tree from "./tree";

// $(document).ready(function () {
//   $("#js-codelist-table").DataTable({
//     paging: false,
//   });

//   $('a[data-toggle="tab"]').on("click", function () {
//     var url = location.href.split("#")[0];

//     if ($(this).attr("href") !== "#about") {
//       url += $(this).attr("href");
//     }

//     history.pushState(null, null, url);
//   });

//   switchToTab();
//   window.addEventListener("hashchange", switchToTab);

//   setUpTree();
// });

document.addEventListener("DOMContentLoaded", function () {
  setUpTree();
});

function switchToTab() {
  var hash = location.hash || "#about";
  $('#tab-list a[href="' + hash + '"]').tab("show");
}

function setUpTree() {
  const hierarchy = new Hierarchy(
    readValueFromPage("parent-map"),
    readValueFromPage("child-map")
  );

  const tree = new Tree(hierarchy, readValueFromPage("expanded-codes"));

  document.addEventListener(
    "click",
    function (e) {
      if (!e.target.matches(".js-toggle-show-descendants")) return;
      e.preventDefault();
      tree.toggleShowDescendants(e);
    },
    false
  );
}
