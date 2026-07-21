(function () {
  let currentMap = null;
  let currentMapContainer = null;
  let currentOverlays = [];

  function clearMapContainer(container) {
    if (!container) {
      return;
    }

    container.innerHTML = "";
    container.classList.remove("map_load_error", "is_loaded");
  }

  function clearMapOverlays() {
    currentOverlays.forEach(function (overlay) {
      if (overlay && typeof overlay.setMap === "function") {
        overlay.setMap(null);
      }
    });
    currentOverlays = [];
  }

  function showEmptyState(container) {
    if (!container) {
      return;
    }

    clearMapContainer(container);
    clearMapOverlays();
    currentMap = null;
    currentMapContainer = null;
    container.innerHTML = '<div class="dashboard_map_empty"><span>🗺️</span><strong>표시할 탐지 위치가 없습니다.</strong><small>탐지 이벤트가 발생하면 지도에 위치가 표시됩니다.</small></div>';
  }

  function ensureMapInstance(container) {
    if (!currentMap || currentMapContainer !== container) {
      clearMapOverlays();
      clearMapContainer(container);
      currentMap = new kakao.maps.Map(container, {
        center: new kakao.maps.LatLng(36.3288, 127.423),
        level: 5,
      });
      currentMapContainer = container;
    } else {
      clearMapOverlays();
      container.classList.remove("map_load_error");
    }

    return currentMap;
  }

  function getMapViewData(data, viewMode) {
    const safeData = Array.isArray(data) ? data : [];

    if (viewMode !== "recent") {
      return safeData;
    }

    if (safeData.length === 0) {
      return [];
    }

    const latestTarget = safeData.reduce(function (currentTarget, candidateTarget) {
      const currentDate = currentTarget && currentTarget.reg_date ? Date.parse(currentTarget.reg_date) : NaN;
      const candidateDate = candidateTarget && candidateTarget.reg_date ? Date.parse(candidateTarget.reg_date) : NaN;

      if (Number.isNaN(candidateDate) && Number.isNaN(currentDate)) {
        return currentTarget;
      }

      if (Number.isNaN(candidateDate)) {
        return currentTarget;
      }

      if (Number.isNaN(currentDate) || candidateDate > currentDate) {
        return candidateTarget;
      }

      return currentTarget;
    }, safeData[0]);

    return latestTarget ? [latestTarget] : [];
  }

  function renderDashboardMap(data, options) {
    const container = document.getElementById("dashboardMap");
    const renderOptions = options || {};
    const autoFocus = renderOptions.autoFocus === true;
    const viewMode = renderOptions.viewMode === "recent" ? "recent" : "all";
    const viewData = getMapViewData(data, viewMode);

    if (!container) {
      return;
    }

    if (!Array.isArray(viewData) || viewData.length === 0) {
      showEmptyState(container);
      return;
    }

    if (!window.kakao || !window.kakao.maps) {
      clearMapContainer(container);
      container.classList.add("map_load_error");
      container.innerHTML = "<div>지도를 불러오지 못했습니다.</div>";
      return;
    }

    const map = ensureMapInstance(container);
    const firstTarget = viewData[0];
    const bounds = new kakao.maps.LatLngBounds();
    let openedInfoWindow = null;

    viewData.forEach(function (target) {
      const currentPosition = new kakao.maps.LatLng(target.latitude, target.longitude);
      bounds.extend(currentPosition);

      const markerOptions = {
        map: map,
        position: currentPosition,
      };

      let marker = new kakao.maps.Marker(markerOptions);
      if (target.image) {
        marker.setImage(new kakao.maps.MarkerImage(dashboardMapImageBaseUrl + target.image, new kakao.maps.Size(44, 44)));
      }
      currentOverlays.push(marker);

      const linePath = [];

      (target.logs || []).forEach(function (log) {
        const point = new kakao.maps.LatLng(log.latitude, log.longitude);
        linePath.push(point);
        bounds.extend(point);
      });

      if (linePath.length > 1) {
        const polyline = new kakao.maps.Polyline({
          map: map,
          path: linePath,
          strokeWeight: 3,
          strokeColor: target.color,
          strokeOpacity: 0.75,
          strokeStyle: "solid",
        });
        currentOverlays.push(polyline);
      }

      const infoWindow = new kakao.maps.InfoWindow({
        content: `
                    <div class="dashboard_map_info">
                        <strong>${target.name}</strong>
                        <span>${target.short_description || "탐지 대상"}</span>
                        <small>${target.reg_date || ""}</small>
                    </div>
                `,
      });

      kakao.maps.event.addListener(marker, "click", function () {
        if (openedInfoWindow === infoWindow) {
          infoWindow.close();
          openedInfoWindow = null;
          return;
        }

        if (openedInfoWindow) {
          openedInfoWindow.close();
        }

        infoWindow.open(map, marker);
        openedInfoWindow = infoWindow;
      });
    });

    if (autoFocus && viewData.length > 1) {
      map.setBounds(bounds, 38, 38, 38, 38);
    } else if (autoFocus) {
      map.setCenter(new kakao.maps.LatLng(firstTarget.latitude, firstTarget.longitude));
    }

    kakao.maps.event.addListener(map, "idle", function () {
      container.classList.add("is_loaded");
    });
  }

  window.renderDashboardMap = renderDashboardMap;
  renderDashboardMap(window.dashboardMapData || []);
})();
