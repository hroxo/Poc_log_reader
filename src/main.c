#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include "utils/header.h"

// Global flag to indicate if the program should exit
sig_atomic_t	g_running = 1;

void	handle_signal(int sig)
{
	(void)sig;
	g_running = 0;
}

int	main(int argc, char **argv)
{
	if (argc < 2 || argc > 3)
	{
		fprintf(stderr, "Usage: %s <log_file_path> [output_file]\n", argv[0]);
		return (EXIT_FAILURE);
	}

	// Setup signal handler for graceful exit
	signal(SIGINT, handle_signal);
	signal(SIGTERM, handle_signal);

	// Disable stdout buffering to ensure immediate output
	setbuf(stdout, NULL);

	printf("=== SCO Monitor ===\n");
	printf("Monitoring: %s\n", argv[1]);
	if (argc == 3)
		printf("Output: %s\n", argv[2]);
	printf("Press Ctrl+C to stop.\n\n");

	start_monitoring(argv[1], (argc == 3) ? argv[2] : NULL);


	return (EXIT_SUCCESS);
}