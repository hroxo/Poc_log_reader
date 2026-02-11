#include "utils/header.h"

extern sig_atomic_t g_running;

#define MSG_BUF_INIT 4096

typedef struct s_parse_state
{
	char	*buffer;
	size_t	buf_size;
	size_t	buf_len;
	int		in_message;
}	t_parse_state;

static void	init_state(t_parse_state *state)
{
	state->buffer = NULL;
	state->buf_size = 0;
	state->buf_len = 0;
	state->in_message = 0;
}

static void	reset_state(t_parse_state *state)
{
	free(state->buffer);
	state->buffer = NULL;
	state->buf_size = 0;
	state->buf_len = 0;
	state->in_message = 0;
}

static int	append_line(t_parse_state *state, const char *line)
{
	size_t	line_len;
	size_t	new_size;
	char	*new_buf;

	line_len = strlen(line);
	if (state->buf_len + line_len + 1 > state->buf_size)
	{
		new_size = (state->buf_size == 0) ? MSG_BUF_INIT : state->buf_size * 2;
		while (new_size < state->buf_len + line_len + 1)
			new_size *= 2;
		new_buf = realloc(state->buffer, new_size);
		if (!new_buf)
			return (-1);
		state->buffer = new_buf;
		state->buf_size = new_size;
	}
	memcpy(state->buffer + state->buf_len, line, line_len);
	state->buf_len += line_len;
	state->buffer[state->buf_len] = '\0';
	return (0);
}

static void	process_message(t_parse_state *state, FILE *output_file)
{
	t_log_entry	*entry;

	if (!state->buffer || state->buf_len == 0)
	{
		reset_state(state);
		return ;
	}
	entry = extract_info(state->buffer);
	if (entry)
	{
		convert_to_json(entry, output_file);
		free_log_entry(entry);
	}
	reset_state(state);
}

static void	process_line(const char *line, t_parse_state *state,
	FILE *output_file)
{
	int	msg_start;
	int	msg_end;

	msg_start = (strstr(line, "[ScoAdapter] CONTENT [<message") != NULL)
		|| (strstr(line, "<message name=\"EnterAssistMode\"") != NULL)
		|| (strstr(line, "<message name=\"ExitAssistMode\"") != NULL);
	msg_end = (strstr(line, "</message>") != NULL);
	if (state->in_message)
	{
		if (msg_start)
		{
			process_message(state, output_file);
			append_line(state, line);
			state->in_message = 1;
			if (msg_end)
				process_message(state, output_file);
		}
		else if (msg_end)
		{
			append_line(state, line);
			process_message(state, output_file);
		}
		else
			append_line(state, line);
	}
	else if (msg_start)
	{
		append_line(state, line);
		state->in_message = 1;
		if (msg_end)
			process_message(state, output_file);
	}
}

static int	drain_lines(int fd, t_parse_state *state, FILE *output_file)
{
	char	*line;
	int		count;

	count = 0;
	while (g_running)
	{
		line = get_next_line(fd);
		if (!line)
			break ;
		process_line(line, state, output_file);
		free(line);
		count++;
	}
	return (count);
}

static void	consume_inotify(int inotify_fd)
{
	char	buf[sizeof(struct inotify_event) + 256];

	while (read(inotify_fd, buf, sizeof(buf)) > 0)
		;
}

void	start_monitoring(const char *log_file_path)
{
	int				fd;
	t_parse_state	state;
	FILE			*output_file;
	int				inotify_fd;
	int				watch_fd;
	struct pollfd	pfd;

	fd = open(log_file_path, O_RDONLY);
	if (fd < 0)
	{
		perror("Error opening log file");
		return ;
	}
	if (lseek(fd, 0, SEEK_END) == -1)
	{
		perror("Error seeking to end of file");
		close(fd);
		return ;
	}
	{
		char	*discard;

		while ((discard = get_next_line(fd)) != NULL)
			free(discard);
	}
	inotify_fd = inotify_init1(IN_NONBLOCK);
	if (inotify_fd < 0)
	{
		perror("Error initializing inotify");
		close(fd);
		return ;
	}
	watch_fd = inotify_add_watch(inotify_fd, log_file_path, IN_MODIFY);
	if (watch_fd < 0)
	{
		perror("Error adding inotify watch");
		close(inotify_fd);
		close(fd);
		return ;
	}
	output_file = fopen("output.json", "a");
	if (!output_file)
	{
		perror("Error opening output.json");
		inotify_rm_watch(inotify_fd, watch_fd);
		close(inotify_fd);
		close(fd);
		return ;
	}
	init_state(&state);
	pfd.fd = inotify_fd;
	pfd.events = POLLIN;
	while (g_running)
	{
		drain_lines(fd, &state, output_file);
		if (poll(&pfd, 1, 200) > 0)
			consume_inotify(inotify_fd);
	}
	if (state.in_message)
		process_message(&state, output_file);
	reset_state(&state);
	fclose(output_file);
	inotify_rm_watch(inotify_fd, watch_fd);
	close(inotify_fd);
	close(fd);
}
