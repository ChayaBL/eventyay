const resultsSelector = ".event-log-results";
let activeRequest;
let requestVersion = 0;

async function loadResults(url, updateHistory = false) {
    const version = ++requestVersion;
    activeRequest?.abort();
    activeRequest = new AbortController();

    try {
        const response = await fetch(url, {
            credentials: "same-origin",
            signal: activeRequest.signal,
            headers: { "X-Requested-With": "XMLHttpRequest" }
        });
        if (!response.ok) throw new Error("Could not load event logs");

        const html = await response.text();
        if (version !== requestVersion) return;

        const documentFragment = new DOMParser().parseFromString(html, "text/html");
        const results = documentFragment.querySelector(resultsSelector);
        const current = document.querySelector(resultsSelector);
        if (!results || !current) {
            window.location.assign(url);
            return;
        }

        current.replaceWith(results);
        if (updateHistory) {
            window.history.pushState({}, "", url);
        }
    } catch (error) {
        if (error.name === "AbortError" || version !== requestVersion) return;
        window.location.assign(url);
    }
}

document.addEventListener("submit", (event) => {
    const form = event.target.closest(".event-log-search-form");
    if (!form) return;

    event.preventDefault();
    const url = new URL(form.getAttribute("action") || window.location.pathname, window.location.origin);
    const params = new URLSearchParams(new FormData(form));
    if (!params.has("page_size")) {
        const currentPageSize = new URLSearchParams(window.location.search).get("page_size");
        if (currentPageSize) params.set("page_size", currentPageSize);
    }
    params.delete("page");
    url.search = params.toString();
    loadResults(url, true);
});

document.addEventListener("click", (event) => {
    const link = event.target.closest(".event-log-results .pagination a[href], .event-log-results a[href*='page_size=']");
    if (!link) return;

    const url = new URL(link.href, window.location.origin);
    if (url.origin !== window.location.origin) return;
    event.preventDefault();
    loadResults(url, true);
});

window.addEventListener("popstate", () => loadResults(window.location.href));
