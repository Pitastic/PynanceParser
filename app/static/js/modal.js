/*
 * Modal
 *
 * Pico.css - https://picocss.com
 * Copyright 2019-2024 - Licensed under MIT
 */

// Config
const isOpenClass = "modal-is-open";
const openingClass = "modal-is-opening";
const closingClass = "modal-is-closing";
const scrollbarWidthCssVar = "--pico-scrollbar-width";
const animationDuration = 400; // ms
let visibleModal = null;

// Toggle modal
const toggleModal = (event) => {
    event.preventDefault();
    const modal = document.getElementById(event.currentTarget.dataset.target);
    const tx = event.currentTarget.dataset.tx;
    const collection = event.currentTarget.dataset.collection;
    if (!modal) return;
    modal && (modal.open ? closeModal(modal) : openModal(modal, event));
};

// Open modal
const openModal = (modal, event) => {
    const { documentElement: html } = document;
    const scrollbarWidth = getScrollbarWidth();
    if (scrollbarWidth) {
        html.style.setProperty(scrollbarWidthCssVar, `${scrollbarWidth}px`);
    }

    // Vorbereitungen
    if (event.currentTarget.dataset.tx) {
		  // Use AJAX to fetch and populate details for the transaction with the given ID
      const tx = event.currentTarget.dataset.tx;
		  console.log('Fetching details for transaction hash: ' + tx);
        resetDetails();
        getInfo(tx, fillTxDetails);
    }

    if (['cat-popup', 'tag-popup'].includes(modal.id)) {
        // Clear Inputs in Modal
        document.getElementById('custom-tag').value = "";
        document.getElementById('custom-cat').value = "";
    }

    // Place Iban from dataset into Input field or clean it
    if (modal.id == "add-iban"){
      const iban_input = document.getElementById("iban-input");
      const link_open = document.querySelector("#add-iban footer a.contrast");
      if (event.currentTarget.dataset.iban) {
        iban_input.value = event.currentTarget.dataset.iban;
        link_open.href = '/' + encodeURIComponent(event.currentTarget.dataset.group);
        link_open.classList.remove('hide');
      } else {
        iban_input.value = "";
        link_open.classList.add('hide');
      }
    }

    // Place Groupname from dataset into Input field or clean it
    if (modal.id == "add-group") {
      const group_input = document.getElementById("groupname-input");
      const link_open = document.querySelector("#add-group footer a.contrast");
      if (event.currentTarget.dataset.group) {
        group_input.value = event.currentTarget.dataset.group;
        link_open.href = '/' + encodeURIComponent(event.currentTarget.dataset.group);
        link_open.classList.remove('hide');
      } else {
        group_input.value = "";
        link_open.classList.add('hide');
      }
    }

    // Open
    html.classList.add(isOpenClass, openingClass);
    setTimeout(() => {
        visibleModal = modal;
        html.classList.remove(openingClass);
    }, animationDuration);
    modal.showModal();
};

// Close modal
const closeModal = (modal) => {
  visibleModal = null;
  const { documentElement: html } = document;
  html.classList.add(closingClass);
  setTimeout(() => {
    html.classList.remove(closingClass, isOpenClass);
    html.style.removeProperty(scrollbarWidthCssVar);
    modal.close();
  }, animationDuration);
  if (modal.id == 'details-popup') {
    resetDetails();
  }
};

// Close with a click outside
document.addEventListener("click", (event) => {
  if (visibleModal === null) return;
  const modalContent = visibleModal.querySelector("article");
  const isClickInside = modalContent.contains(event.target);
  !isClickInside && closeModal(visibleModal);
});

// Close with Esc key
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && visibleModal) {
    closeModal(visibleModal);
  }
});

// Get scrollbar width
const getScrollbarWidth = () => {
  const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
  return scrollbarWidth;
};

// Is scrollbar visible
const isScrollbarVisible = () => {
  return document.body.scrollHeight > screen.height;
};
