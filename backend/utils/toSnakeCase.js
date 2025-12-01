const toSnakeCase = (text) => {
	return text
		.replace(/[\s-]+/g, '_') // replaces spaces with underscores
		.replace(/([a-z0-9])([A-Z])/g, '$1_$2')
		.toLowerCase(); // convert everything to lowercase

}

export default toSnakeCase;