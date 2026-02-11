/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   get_next_line_bonus.c                              :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: hroxo <hroxo@student.42porto.com>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2025/10/20 14:00:53 by hroxo             #+#    #+#             */
/*   Updated: 2025/11/25 15:25:00 by hroxo            ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "header.h"

extern sig_atomic_t g_running;

char	*join_n_free(char *str, char *buf)
{
	char	*out;

	if (!buf[0] || !*buf)
		return (str);
	out = ft_glstrjoin(str, buf);
	if (!out)
	{
		free(str);
		return (NULL);
	}
	free(str);
	return (out);
}

char	*read_file(char *stash, int fd)
{
	char	*buf;
	int		f_r;

	if (has_nl(stash))
		return (stash);
	f_r = 1;
	buf = ft_glcalloc(BUFFER_SIZE + 1, sizeof(char));
	if (!buf)
		return (NULL);
	while (!has_nl(stash))
	{
		f_r = read(fd, buf, BUFFER_SIZE);

		if (!g_running) { // Check global flag after read
			free(stash);
			free(buf);
			return (NULL);
		}
		if (f_r == 0)
		{
			free(buf);
			return (stash);
		}
		if (f_r < 0) // Error reading file
		{
			free(stash);
			free(buf);
			return (NULL);
		}
		buf[f_r] = 0;
		stash = join_n_free(stash, buf);
	}
	free(buf);
	return (stash);
}

char	*get_the_line(char *stash)
{
	size_t	len;
	char	*line;

	if (!stash[0])
		return (NULL);
	len = 0;
	while (stash[len] && stash[len] != '\n')
		len++;
	if (stash[len] == '\n')
		len++;
	line = malloc(len + 1);
	if (!line)
		return (NULL);
	memcpy(line, stash, len);
	line[len] = 0;
	return (line);
}

char	*update_stash(char *stash)
{
	size_t	nl_pos;
	size_t	total_len;
	size_t	remain;
	char	*new_stash;

	nl_pos = 0;
	while (stash[nl_pos] && stash[nl_pos] != '\n')
		nl_pos++;
	if (stash[nl_pos] == '\n')
		nl_pos++;
	total_len = ft_glstrlen(stash);
	remain = total_len - nl_pos;
	new_stash = malloc(remain + 1);
	if (!new_stash)
		return (NULL);
	memcpy(new_stash, stash + nl_pos, remain);
	new_stash[remain] = 0;
	free(stash);
	return (new_stash);
}

char	*get_next_line(int fd)
{
	static char	*stash[4096];
	char		*line;

	if (fd < 0 || BUFFER_SIZE <= 0)
		return (NULL);
	stash[fd] = read_file(stash[fd], fd);
	if (!stash[fd])
		return (NULL);
	if (!ft_glstrlen(stash[fd]) || !strchr(stash[fd], '\n'))
		return (NULL);
	line = get_the_line(stash[fd]);
	if (!line)
	{
		free(stash[fd]);
		stash[fd] = NULL;
		return (NULL);
	}
	stash[fd] = update_stash(stash[fd]);
	if (stash[fd][0] == 0)
	{
		free(stash[fd]);
		stash[fd] = NULL;
	}
	return (line);
}
