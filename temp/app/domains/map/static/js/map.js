// console.log("카카오맵 객체:", window.kakao);
// console.log(maps);

// 0. 타겟 선택 드롭다운(select) 요소 가져오기
const select = document.getElementById('targetSelect');

// 0-1. maps 배열을 순회하며 드롭다운에 타겟 옵션 추가
maps.forEach(target => {
        const option = document.createElement('option');

        option.value = target.id;
        option.textContent = target.name;

        select.appendChild(option);

});

// 1. 지도를 띄울 중심좌표 (첫번째 타겟 기준)
const centerlat = maps[0].latitude;
const centerlng = maps[0].longitude;

//2. 지도 확대 레벨- n-1번 확대된다.
const options = {
        center: new kakao.maps.LatLng(centerlat, centerlng),
        level: 4
};

//3. HTML에서 지도를 담을 컨테이너(div)를 가져와 실제 지도 객체 생성
var container = document.getElementById("map");
var map = new kakao.maps.Map(container, options);

//4. 마커 객체 생성
// 현재 열려있는 InfoWindow를 추적하는 변수 (동시에 여러개 열리지 않게 제어)
let openedInfoWindow = null;

// 마커/폴리라인을 타겟 id와 함께 저장해둘 배열 (드롭다운 필터링에 사용)
const targetobjects = [];

maps.forEach(function(target){
        
        
        // 마커에 사용할 커스텀 이미지(MarkerImage) 생성
        const imageSrc = `${imageBaseUrl}${target.image}`;
        
        const imageSize = new kakao.maps.Size(60, 60);
        
        const markerImage = new kakao.maps.MarkerImage(
                imageSrc,
                imageSize
        );
        
        // 5. 타겟 위치에 커스텀 이미지 마커 생성 및 지도에 표시
        const marker = new kakao.maps.Marker({
                map: map,
                position: new kakao.maps.LatLng(
                        target.latitude,
                        target.longitude
                ),
                image: markerImage
                
        });
        
        // eventlog에 찍힌 좌표들을 담는 linepath라는 배열을 생성
        const linePath = [];
        
        // 타겟의 이동 로그(logs)를 순회하며 좌표(LatLng)로 변환해 linePath에 추가
        target.logs.forEach(function(log){
                
                linePath.push(
                        new kakao.maps.LatLng(
                                log.latitude,
                                log.longitude
                        )
                );
        });
        console.log(target.id);
        console.log(target.logs);
        console.log(linePath);
        
        //linepath에 담긴 좌표들을 가지고 kakaomap 위에 polyline 생성
        // (타겟의 이동 경로를 선으로 표시)
        const polyline = new kakao.maps.Polyline({
                
                path: linePath,
                
                strokeWeight: 2,
                
                strokeColor: target.color,
                
                strokeOpacity: 0.5,
                
                strokeStyle: 'solid'
        });
        polyline.setMap(map);

        // 생성한 마커/폴리라인을 타겟 id와 묶어서 배열에 저장
        // (나중에 드롭다운에서 특정 타겟만 보이게/숨기게 하기 위함)
        targetobjects.push({
                id: target.id,
                marker: marker,
                polyline: polyline
        });

        // REG_DATE 분리>>날짜/시간
        // (예: "2025-01-01,12:00:00" 형태의 문자열을 콤마 기준으로 분리)
        const[date, time] = target.reg_date.split(",");

        //6. Infowindow 내용
        // 타겟 이미지, 이름, 나이, 설명, 탐지일/탐지시간을 담은 HTML 구성
        const content = `
        
            <div class = "info-window">
                <img class="full_image"
                src="${imageBaseUrl}${target.image}">
                <h3>${target.name}</h3>
                <p>나이: ${target.age}</p>
                <p><strong>${target.short_description}</strong></p>
                
                <p>탐지일</p>
                <p>${date}</p>
                
                <p>탐지시간</p>
                <p>${time}</p>
            </div>
        `;
        
        //7. InfoWindow 생성
        const infoWindow = new kakao.maps.InfoWindow({
                content: content
        });
        //8. 마커 클릭시 열고닫기
        kakao.maps.event.addListener(marker, 'click', function() {
                
                // 이미 해당 마커의 InfoWindow가 열려있다면 닫기 (토글)
                if(openedInfoWindow === infoWindow){
                        infoWindow.close();
                        openedInfoWindow = null;
                        return;
                }
                // 다른 InfoWindow가 열려있다면 먼저 닫기 (한번에 하나만 열리게)
                if (openedInfoWindow) {
                    openedInfoWindow.close();
                }
                // 현재 클릭한 마커의 InfoWindow 열기
                infoWindow.open(map, marker);
                openedInfoWindow = infoWindow;
        });
});

// 9. 드롭다운(select) 값이 바뀔 때마다 실행되는 이벤트 리스너
// 모든 타겟의 마커/폴리라인 생성이 끝난 뒤, 루프 밖에서 딱 한 번만 등록
// 선택한 타겟의 마커/폴리라인만 지도에 보이고 나머지는 숨김
// (전체 선택 시 "" 값이면 전부 다시 표시)
select.addEventListener("change", function () {
        const selected = this.value;

        targetobjects.forEach(obj => {
                if (selected === "") {
                   obj.marker.setMap(map);
                   obj.polyline.setMap(map);
                } else if (obj.id === selected) {
                   obj.marker.setMap(map);
                   obj.polyline.setMap(map);

                } else {
                   obj.marker.setMap(null);
                   obj.polyline.setMap(null);
                }
        });
});