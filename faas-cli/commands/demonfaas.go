package commands

import (
	"fmt"

	"github.com/spf13/cobra"
)

const DEBUG = true

func d_print(strs ...interface{}) {
	if !DEBUG {
		return
	}
	fmt.Println(strs...)
}

func d_assert(predicate bool) {
	if !DEBUG {
		return
	}
	if !predicate {
		panic("assertion failed")
	}
}

var (
	flag1 int
	flag2 bool
)

func init() {
	d_print("demonfaas init")

	demonfaasCmd.Flags().IntVarP(&flag1, "flag1", "1", 0, "flag1 test")
	demonfaasCmd.Flags().BoolVarP(&flag2, "flag2", "2", false, "flag2 test")

	faasCmd.AddCommand(demonfaasCmd)
}

var demonfaasCmd = &cobra.Command{
	Use:      `demonfaas`, // needs to match file name
	Short:    `fill me in`,
	Long:     `fill me in`,
	Example:  `fill me in`,
	PreRunE:  preRun,
	RunE:     run,
	PostRunE: postRun,
}

func preRun(cmd *cobra.Command, args []string) error {
	return nil
}

func run(cmd *cobra.Command, args []string) error {
	return nil
}

func postRun(cmd *cobra.Command, args []string) error {
	return nil
}
