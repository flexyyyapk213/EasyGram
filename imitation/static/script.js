let commands = []

document.addEventListener('DOMContentLoaded', function(){
	fetch('/getCommands', {
		method: 'GET',
		headers: {
            'Content-Type': 'application/json',
        }
	}).then(response => {
		if(response.status === 204) return;
		return response.json()
	}).then(update => {
		commands.push(update)

		let listCommands = document.querySelector('.listCommands')

        if (update === undefined)
            return;

		update.forEach(command => {
			let buttonCommand = document.createElement('button')
			buttonCommand.onclick = function(){sendCommand(command.command)}
			buttonCommand.innerHTML = `<b>${command.command}</b> - ${command.description}`
			buttonCommand.classList.add('command')
			listCommands.appendChild(buttonCommand)
		})
	})

	fetch('/getBotData', {
		method: 'GET',
		headers: {
            'Content-Type': 'application/json',
        }
	}).then(response => {
		if(response.status === 204) return;
		return response.json()
	}).then(data => {
		let name = document.getElementById('name')
		let username = document.getElementById('username')
		let description = document.getElementById('description')
		let ava = document.getElementById('photo')

        name.innerText = data !== undefined ? data.name : "Бот"
		username.innerText = data !== undefined ? `@${data.username}` : '@oprosmenya'

		if (data !== undefined) {
            if(data.description){
                description.innerText = data.description
            }else{
                description.innerText = 'Имитированный бот🤖'
            }
            if(data.image){
                ava.style.background = `url(${data.image}) center no-repeat, linear-gradient(135deg, #6cb2f7, #b3dafe)`
                ava.style.backgroundSize = 'cover'
            }
        }
	})

	let history = document.querySelector('.history')
	let send = document.getElementById('sendMessage')
    let userInput = document.getElementById('inputText')
    let _commands = document.querySelector('.commands')
    let images = document.querySelector('.images')

    userInput.addEventListener('input', function(event){
        let count = (userInput.value.match(/\n/g) || []).length

        if (count / 2 > 0) {
            console.log("work")
            userInput.style.height = 41*count + "px"
            send.style.height = 41*count + "px"
            _commands.style.height = 41*count + "px"
            images.style.height = 41*count + "px"
        } else {
            userInput.style.height = "41px"
            send.style.height = "41px"
            _commands.style.height = "41px"
            images.style.height = "41px"
        }

        history.scrollTop = history.scrollHeight;
    })

	document.addEventListener('keydown', function(event){
		if(event.ctrlKey && event.key === 'Enter' && document.activeElement === userInput){
			sendMessage()
		}
	})

	send.addEventListener('click', function(){
		sendMessage()
	})

    let fileInput = document.getElementById('fileInput')

    fileInput.addEventListener('change', function(event) {
        let file = fileInput.files[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            alert('Пожалуйста, выберите изображение!');
            return;
        }
        
        let reader = new FileReader();
        reader.onload = function(e) {
            let userInput = document.getElementById('inputText')

            let base64 = e.target.result
            fetch('/sendMessage', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({image: base64, caption: userInput.value.length > 0 ? userInput.value : null})
            })

            let history = document.querySelector('.history')
            let user = document.createElement('div')
            user.classList.add('user')

            let _image = document.createElement('img')
            _image.src = e.target.result
            _image.alt = userInput.value
            _image.style.width = 'auto'
            _image.style.height = 'auto'
            user.appendChild(_image)

            let caption = document.createElement('div');
            caption.innerText = userInput.value;
            caption.style.marginTop = '8px';
            user.appendChild(caption);

            userInput.value = ""

            userInput.style.height = "41px"
            send.style.height = "41px"
            _commands.style.height = "41px"
            images.style.height = "41px"
            history.scrollTop = history.scrollHeight;

            history.appendChild(user)
        }
        reader.readAsDataURL(file);
    })
})

function sendMessage(message){
	console.log(message)
	let userInput = document.getElementById('inputText')
	let history = document.querySelector('.history')

	if(!userInput.value && message === undefined){
		return alert('Напишите текст')
	}

	let user = document.createElement('div')
	user.classList.add('user')
	user.innerHTML = message === undefined ? userInput.value : message

	fetch('/sendMessage', {
		method: 'POST',
		headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({'text': message === undefined ? userInput.value : message})
	}).then(response => response.json()).then(data => {
		let message_id = data.message_id
		user.id = `${message_id}`
	});

	history.appendChild(user)
	userInput.value = ''
	history.scrollTop = history.scrollHeight
}

function get_response() {
	let history = document.querySelector('.history');

	fetch('/getUpdates', {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
		},
	}).then(response => {
		if (response.status === 204) return;
		return response.json();
	}).then(data => {
		if (data && data.updates) {
			data.updates.forEach(update => {
				if('message' in update){
					let bot = document.createElement('div');
					bot.classList.add('bot');
					bot.id = `${update.message.message_id}`

					if(update.message.parse_mode == 'html'){
						bot.textContent = update.message.text;
					}else if(update.message.parse_mode == 'markdown'){
						bot.textContent = update.message.text
					}else{
						bot.innerText = update.message.text
					}

                    if (update.message.inline.length !== 0) {
                        for (let i = 0; i < update.message.inline.length; i++) {
                            let row = document.createElement('div')
                            row.style.display = 'flex'
                            row.style.flexDirection = 'column'
                            row.style.alignItems = 'center'

                            for (let j = 0; j < update.message.inline[i].length; j++) {
                                let btn = document.createElement('button')
                                btn.innerText = update.message.inline[i][j].text
                                row.appendChild(btn)
                            }

                            history.appendChild(row)
                        }
                    }

					history.appendChild(bot)

					history.scrollTop = history.scrollHeight
				}else if('set_commands' in update){
					commands.push(update.set_commands)

					let listCommands = document.querySelector('.listCommands')
					console.log(commands)

					update.set_commands.forEach(command => {
						let buttonCommand = document.createElement('button')
						buttonCommand.onClick = `sendCommand(${command.command})`
						buttonCommand.innerHTML = `<b>${command.command}</b> - ${command.description}`
						buttonCommand.classList.add('command')
						listCommands.appendChild(buttonCommand)
					})
				}else if('photo' in update){
					let bot = document.createElement('div')
					bot.classList.add('bot')
					bot.id = `${update.photo.message_id}`

					let img = document.createElement('img')
					img.src = `data:image/jpeg;base64,${update.photo.photo}`
					img.alt = 'Фото'
					img.style.width = '95%'
					img.style.height = 'auto'
					img.style.borderRadius = '10px'
					img.style.margin = '10px'
					img.style.objectFit = 'cover'
					img.style.objectPosition = 'center'
					img.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.1)'
					img.style.transition = 'transform 0.3s ease'
					img.style.cursor = 'pointer'
					bot.appendChild(img)

					if(update.photo.caption){
						let caption = document.createElement('div')
						caption.id = 'caption'
						caption.textContent = update.photo.caption
						bot.appendChild(caption)
					}

                    if (update.message.inline.length !== 0) {
                        for (let i = 0; i < update.message.inline.length; i++) {
                            let row = document.createElement('div')
                            row.style.display = 'flex'
                            row.style.flexDirection = 'column'
                            row.style.alignItems = 'center'

                            for (let j = 0; j < update.message.inline[i].length; j++) {
                                let btn = document.createElement('button')
                                btn.innerText = update.message.inline[i][j].text
                                row.appendChild(btn)
                            }

                            history.appendChild(row)
                        }
                    }

					history.appendChild(bot)
				}else if('delete_message' in update){
					let message = document.getElementById(update.delete_message.message_id.toString())
					if(message){
						message.remove()
					}
				}else if('edit_message_text' in update){
					let message = document.getElementById(update.edit_message_text.message_id.toString())
					if(message){
						let parent_msg = message.querySelector('#caption')

						if(parent_msg){
							parent_msg.textContent = update.edit_message_text.text
						}else{
							message.textContent = update.edit_message_text.text
						}

						let status = document.createElement('div')
						status.textContent = 'изменено'
						status.style.color = 'gray'
						status.style.fontSize = '12px'
						message.appendChild(status)
					}
				}else if('poll' in update){
					let bot = document.createElement('div')
					bot.classList.add('bot')
					bot.id = `${update.poll.message_id}`
					bot.innerHTML = `<h4>${update.poll.question}</h4>`

					bot.innerHTML += `<br>`

                    console.log(update.poll)
					
					if(!update.poll.allows_multiple_answers){
						update.poll.options.forEach(option => {
							let input = document.createElement('input')
							input.innerText = option.text
							input.type = 'radio'
							input.name = `poll_${update.poll.message_id}`
							input.value = option.text
							input.id = `poll_${update.poll.message_id}_${option.text}`
							
							let label = document.createElement('label')
							label.for = `poll_${update.poll.message_id}_${option.text}`
							label.textContent = option.text
							
							bot.appendChild(input)
							bot.appendChild(label)
							bot.innerHTML += `<br>`
						})
					}else{
						for(let i = 0; i < update.poll.options.length; i++){
							let input = document.createElement('input')
							input.innerText = update.poll.options[i].text
							input.type = 'checkbox'
							input.name = `poll_${update.poll.message_id}_${i}`
							input.value = update.poll.options[i].text
							input.id = `poll_${update.poll.message_id}_${i}`
							
							let label = document.createElement('label')
							label.for = `poll_${update.poll.message_id}_${i}`
							label.textContent = update.poll.options[i].text

							bot.appendChild(input)
							bot.appendChild(label)
							bot.innerHTML += `<br>`
						}
					}

                    let btns = document.createElement('div')
                    btns.classList.add('buttons')

                    if (update.poll.inline.length !== 0) {
                        for (let i = 0; i < update.poll.inline.length; i++) {
                            let row = document.createElement('div')
                            row.style.display = 'flex'
                            row.style.width = '50%'
                            row.style.gap = '1px'
                            row.style.marginLeft = '5px'

                            for (let j = 0; j < update.poll.inline[i].length; j++) {
                                let btn = document.createElement('button')
                                btn.innerText = update.poll.inline[i][j].text
                                btn.style.borderRadius = '0px'
                                btn.style.position = 'relative'
                                btn.style.flex = '1 1 0'
                                btn.style.boxSizing = 'border-box'
                                btn.style.minWidth = '0'
                                btn.style.background = 'rgba(0, 0, 0, 0.5)'
                                btn.style.color = 'white'
                                btn.style.borderColor = 'rgba(255, 255, 255, 0)'
                                btn.style.transition = 'background 0.2s, color 0.2s'

                                btn.addEventListener('mouseenter', function() {
                                    btn.style.background = 'rgba(42, 42, 42, 0.2)';
                                    btn.style.color = 'black';
                                })

                                btn.addEventListener('mouseleave', function() {
                                    btn.style.background = 'rgba(0,0,0,0.5)';
                                    btn.style.color = 'white';
                                })

                                btn.addEventListener('mousedown', function() {
                                    btn.style.background = 'rgba(255,255,255,0.3)';
                                    btn.style.color = 'black';
                                })

                                btn.addEventListener('mouseup', function() {
                                    // Можно вернуть к hover-стилю, если мышь всё ещё над кнопкой
                                    btn.style.background = 'rgba(42, 42, 42, 0.2)';
                                    btn.style.color = 'black';
                                })

                                if (update.poll.inline.length === 1 && update.poll.inline[i].length === 1) {
                                    btn.style.borderTopLeftRadius = '10px'
                                    btn.style.borderTopRightRadius = '10px'
                                    console.log('work')
                                } else if (update.poll.inline[i].length === 1 && i === 0) {
                                    btn.style.borderTopLeftRadius = '10px'
                                    btn.style.borderTopRightRadius = '10px'
                                } else if (update.poll.inline[i].length === 1 && i === update.poll.inline.length - 1) {
                                    btn.style.borderBottomLeftRadius = '10px'
                                    btn.style.borderBottomRightRadius = '10px'
                                } else if (i === 0 && j === 0) {
                                    btn.style.borderTopLeftRadius = '10px'
                                } else if (i === 0 && j === update.poll.inline[i].length - 1) {
                                    btn.style.borderTopRightRadius = '10px'
                                } else if (i === update.poll.inline.length - 1 && j === 0) {
                                    btn.style.borderBottomLeftRadius = '10px'
                                } else if (i === update.poll.inline.length - 1 && j === update.poll.inline[i].length - 1) {
                                    btn.style.borderBottomRightRadius = '10px'
                                }

                                btn.style.height = '35px'
                                btn.style.maxHeight = '35px'
                                btn.style.overflow = 'hidden'
                                btn.style.textOverflow = 'ellipsis'
                                btn.style.fontSize = '16px'
                                btn.style.fontFamily = 'bold'
                                row.appendChild(btn)
                            }

                            btns.appendChild(row)
                        }
                    }

					history.appendChild(bot)

                    if (btns.hasChildNodes())
                        history.appendChild(btns)
				}
			});
		}
	}).catch(err => console.error('Ошибка при получении обновлений:', err));
}

function showCommands(){
	if(!commands){
		return;
	}

	let listCommands = document.querySelector('.listCommands')
	let butt = document.getElementById('showCommands')

	if(listCommands.style.display == 'none'){
		listCommands.style.display = 'block'
		butt.innerText = '× меню'
	}else{
		listCommands.style.display = 'none'
		butt.innerText = '/ меню'
	}
}

function sendCommand(command){
	sendMessage(`/${command}`)

	let listCommands = document.querySelector('.listCommands')
	let butt = document.getElementById('showCommands')
	listCommands.style.display = 'none'
	butt.innerText = '/ меню'
}

setInterval(get_response, 1000);