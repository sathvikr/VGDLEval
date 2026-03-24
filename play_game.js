// Post requests

/**
 * @fileoverview
 * Draw lines, polygons, circles, etc on the screen.
 * Render text in a certain font to the screen.
 */
var gamejs = require('gamejs');;
var vgdl_parser = VGDLParser(gamejs);
var game;


var retry_game = function () {
	// $('body').addClass('loading')
	location.reload();

}

var go_back = function () {
	window.location.href = '../..';
}


var continue_game = function () {
	game.paused = true;
	// window.location.href = `./games/${}`
}


var next_level = function () {
	window.location.href = `../../games/${data.real}/${data.pair+1}.html`
}

var prev_level = function () {
	window.location.href = `../../games/${data.real}/${data.pair-1}.html`
}

$(document).on('click', '#return', go_back);
$(document).on('click', '#retry', retry_game);
$(document).on('click', '#continue', continue_game);

$(document).on('click', '#next', next_level);
$(document).on('click', '#prev', prev_level);


$(document).on('click', '#pause', function () {
	game.paused = !game.paused;
	$(this).text(game.paused ? "Resume" : "Pause");
})



$(document).ready(function () {
	game = vgdl_parser.playGame(vgdl_game.game, vgdl_game.level, 0);
	window.game = game;
	console.log("Game initialized. Pause feature enabled.");

	var return_button = $('<button id="return">Return to Games List</button>');
	var next_button = $('<button id="next">Next Level</button>');

	var retry_container = $('<div id="retry-div" class="Flex-Container"></div>');
	var retry_text = $('<p id="retry-text">If you get stuck, you can press "Retry" to reset this level. Also, remember that spacebar may be used.</p>')
	var retry_button = $('<button id="retry">Retry</button>')
	retry_container.append(retry_text)
	retry_container.append(retry_button)

	var end_game_delay = 1000
	var ended = false;

	if (show_score) {
		var score_container = $('<h2 id="score">Score: <span id="score-value">0</span></h2>');
		$('#game-body').prepend(score_container)
	}
	var on_game_end = function () {
		game.paused = true;
		ended = true
		$('#retry-div').remove()
		var show_status = function () {
			var status_text = '';
		    //var last_state1 = game.gameStates.length;

			if (game.win) {
				//game.gameStates[last_state1-1].score += 1;

				var container = $('<div></div>');
				if (!data.next) {
					var button = return_button;
				} else {
					var button = next_button;
				}
			}
			else {
				//game.gameStates[last_state1-1].score -= 1;
				var container = retry_container;
				var button = retry_button;
			}
			
			container.append('<br>')
			container.append(button)

			$('#message').append(container)
			$('#retry-text').remove();
		}	

		if (game.win) {
			$('#title').text('Game Won!')
			//var score_container = $('<h2 id="score">Score: <span id="score-value">0</span></h2>');
			//$('#game-body').prepend(score_container)
			show_status()
			
		} else {
			$('#title').text('Game Lost!')
			//var score_container = $('<h2 id="score">Score: <span id="score-value">0</span></h2>');
			//$('#game-body').prepend(score_container)
			window.setTimeout(show_status, end_game_delay);
		}
	}

	var begin_game = function () {

		$('#start').remove();
		$('#start-llm').remove();
		var pause_button = $('<button id="pause">Pause</button>');
		$('#start-div').append(pause_button);
		game.paused = false;

	}

	var start_llm_game = function () {
		$('#start').remove();
		$('#start-llm').remove();
		var pause_button = $('<button id="pause">Resume</button>');
		$('#start-div').append(pause_button);
		game.paused = true;
		console.log("LLM Mode started. Game paused. Use game.step(action) to proceed.");
	}



	$('#gjs-canvas').focus();
	$('#start').click(begin_game);

	var llm_button = $('<button id="start-llm" style="margin-left: 10px;">Start LLM</button>');
	$('#start-div').append(llm_button);
	$('#start-llm').click(start_llm_game);

	game.paused = true;
	window.game = game;
	gamejs.ready(game.run(on_game_end));
	
});

// // gamejs.ready will call your main function
// // once all components and resources are ready.
// gamejs.ready(main);
