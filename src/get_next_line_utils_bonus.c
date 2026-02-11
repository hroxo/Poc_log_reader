/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   get_next_line_utils_bonus.c                        :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: hroxo <hroxo@student.42porto.com>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2025/10/20 14:27:00 by hroxo             #+#    #+#             */
/*   Updated: 2025/11/25 15:25:14 by hroxo            ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "header.h"

void	*ft_glcalloc(size_t nmemb, size_t size)
{
	void	*out;
	size_t	total;

	if (size > 0 && nmemb > (size_t)(-1) / size)
		return (NULL);
	total = nmemb * size;
	out = malloc(total);
	if (!out)
		return (NULL);
	memset(out, 0, total);
	return (out);
}

size_t	ft_glstrlen(char *str)
{
	size_t	len;

	if (!str)
		return (0);
	len = 0;
	while (str[len])
		len++;
	return (len);
}

char	*ft_glstrjoin(char *s1, char *s2)
{
	char	*big_str;
	size_t	len1;
	size_t	len2;

	len1 = ft_glstrlen(s1);
	len2 = ft_glstrlen(s2);
	big_str = malloc(len1 + len2 + 1);
	if (!big_str)
		return (NULL);
	if (len1)
		memcpy(big_str, s1, len1);
	if (len2)
		memcpy(big_str + len1, s2, len2);
	big_str[len1 + len2] = 0;
	return (big_str);
}

size_t	has_nl(char *str)
{
	if (!str)
		return (0);
	if (strchr(str, '\n'))
		return (1);
	return (0);
}

void	clean_house(char **strs)
{
	size_t	i;

	i = 0;
	while (strs[i])
	{
		free(strs[i]);
		i++;
	}
}
