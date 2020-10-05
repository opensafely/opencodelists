class Tree {
  constructor(hierarchy, expandedCodes) {
    this.hierarchy = hierarchy;
    this.expandedCodes = new Set(expandedCodes);

    this.toggleShowDescendants = this.toggleShowDescendants.bind(this);
    this.showRow = this.showRow.bind(this);
    this.hideRow = this.hideRow.bind(this);
  }

  codeFromElement(e) {
    return e.closest(".js-tree-row").data("code");
  }

  rowFromCode(code) {
    return $(`div.js-tree-row[data-code="${code}"]`);
  }

  isExpanded(code) {
    return this.expandedCodes.has(code);
  }

  toggleShowDescendants(e) {
    console.log("toggleShowDescendants", e);
    const code = this.codeFromElement($(e.target));
    console.log(code);
    if (this.isExpanded(code)) {
      console.log("is expanded");
      this.expandedCodes.delete(code);
      this.hierarchy.getDescendants(code).forEach(this.hideRow);
      this.setToggleIcon(code, "⊞");
    } else {
      console.log("is not expanded");
      this.expandedCodes.add(code);
      this.hierarchy.getDescendants(code).forEach(this.showRow);
      this.setToggleIcon(code, "⊟");
    }
  }

  showRow(code) {
    console.log("showRow", code);
    this.rowFromCode(code).removeClass("d-none").addClass("d-flex");
  }

  hideRow(code) {
    console.log("hideRow", code);
    this.rowFromCode(code).removeClass("d-flex").addClass("d-none");
  }

  setToggleIcon(code, icon) {
    this.rowFromCode(code).find(".js-toggle-show-descendants").html(icon);
  }
}

export { Tree as default };
