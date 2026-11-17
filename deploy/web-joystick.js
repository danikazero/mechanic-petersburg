"use strict";
if (!window.mechanicStick) {
	const state = window.mechanicStick = { id: -1, x: 0, y: 0, starts: 0, drags: 0 };
	const canvas = document.getElementById('canvas');
	const point = event => {
		const box = canvas.getBoundingClientRect();
		const scale = Math.min(box.width / 1152, box.height / 648);
		return {
			x: (event.clientX - box.left - (box.width - 1152 * scale) / 2) / scale,
			y: (event.clientY - box.top - (box.height - 648 * scale) / 2) / scale
		};
	};
	window.addEventListener('pointerdown', event => {
		if (event.target !== canvas || event.pointerType === 'mouse' || state.id !== -1) return;
		const pos = point(event);
		if (pos.x < 24 || pos.x > 188 || pos.y < 462 || pos.y > 626) return;
		Object.assign(state, pos);
		state.id = event.pointerId;
		state.starts++;
	}, true);
	window.addEventListener('pointermove', event => {
		if (event.pointerId !== state.id) return;
		Object.assign(state, point(event));
		state.drags++;
	}, true);
	const release = event => {
		if (event.pointerId === state.id) state.id = -1;
	};
	window.addEventListener('pointerup', release, true);
	window.addEventListener('pointercancel', release, true);
	window.addEventListener('blur', () => { state.id = -1; });
	document.addEventListener('visibilitychange', () => {
		if (document.hidden) state.id = -1;
	});
}
