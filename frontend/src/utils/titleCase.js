export const titleCase = (str) => {
    if (!str) return '';

    const smallWords = ['of', 'the', 'and', 'in', 'on', 'at', 'for', 'with', 'a', 'an', 'to'];

    return str
        .toLowerCase()
        .split(' ')
        .map((word, index) => {
            if (index === 0 || !smallWords.includes(word)) {
                return word.charAt(0).toUpperCase() + word.slice(1);
            }
            return word;
        })
        .join(' ');
};
