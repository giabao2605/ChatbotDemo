// Minimal local Streamlit component bridge.
// Avoids loading streamlit-component-lib from CDN.
window.Streamlit = window.Streamlit || {
  setComponentReady: function () {
    window.parent.postMessage(
      { isStreamlitMessage: true, type: "streamlit:componentReady", apiVersion: 1 },
      "*"
    );
  },
  setFrameHeight: function (height) {
    window.parent.postMessage(
      { isStreamlitMessage: true, type: "streamlit:setFrameHeight", height: height },
      "*"
    );
  },
  setComponentValue: function (value) {
    window.parent.postMessage(
      {
        isStreamlitMessage: true,
        type: "streamlit:setComponentValue",
        value: value,
        dataType: "json",
      },
      "*"
    );
  },
};
